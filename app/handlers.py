import asyncio
import datetime
import logging
import os
import queue
from typing import Union
from aiogram import Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from pydantic_core import ValidationError
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import between, select, insert, exists, delete
from aiogram.fsm.context import FSMContext
from buttons.buttons import BirthdayCallback, Edit, Pagination, edit, get_username_id, paginator, set_notif_date, start as start_buttons, universal_keyboard, lang_data

from config import config
from models.models import Birthdays, Groups, User
from app.query import generate
from app.states import BirthdayState, EditState
from schemas.schema import LangSchema, TimeSchema
from tasks.tasks import get_user, send_notification
from app.queues import MyQueue
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN)

engine = create_async_engine(os.getenv('db_url'))

Session = async_sessionmaker(engine, expire_on_commit=False)

cache = Redis(host=os.getenv('redis_url'), port=6379, db=1)

prompt_with_username = 'Пожалуйста напиши только один образец поздравления на день рождение {} от имени @{}, не менее на 100 слов, не забудь добавить собачку перед именем поздравителя, пусть в ответе будет только само поздравление без никаких дополнительных ответов. Язык{}. Он мне {}'

prompt_without_username = 'Пожалуйста напиши только один образец поздравления на день рождение {} от имени {}, не менее на 100 слов, пусть в ответе будет только само поздравление без никаких дополнительных ответов. Язык{}. Он мне {}'


async def start(message: Message):
    global queue
    queue = MyQueue.get_instance()
    user_id = message.from_user.id
    if not await cache.get(user_id):
        await cache.set(name=user_id, value=user_id)
        asyncio.create_task(get_queue(user_id))
    username = message.from_user.username
    fullname = message.from_user.full_name

    async with Session() as conn:
        user = select(exists().where(User.username == username).__or__(exists().where(User.id == user_id)))
        user = await conn.execute(user)
        user = user.scalar()
        logger.info(f'User exists: {user}')
        if not user:
            logger.info(f'Saving user')
            user = insert(User).values(id=user_id, username=username, full_name=fullname)
            await conn.execute(user)
            await conn.commit()


    await message.answer(f"Привет, {message.from_user.full_name}!", reply_markup=start_buttons)


async def add_birthday(message: Message, state: FSMContext):
    await message.answer("Добавьте день рождениe")
    await message.answer("Присылайте id(нажимая на кнопку) именинника", reply_markup= await get_username_id())
    await state.set_state(BirthdayState.send_username_or_id)


async def username_or_id(message: Message, state: FSMContext, bot: Bot):    
    if message.user_shared:
        birthday_boy_id_username = message.user_shared.user_id
        await state.update_data(birthday_boy_id=birthday_boy_id_username)
    else:
        await message.answer('Введите username или id(нажимая на кнопку) имениника', reply_markup= await get_username_id())
        return
    await message.answer(f'Введите имя:')
    await state.set_state(BirthdayState.full_name)


async def get_full_name(message: Message, state: FSMContext):
    full_name = message.text
    await state.update_data(full_name=full_name)
    await message.answer('Выберите✅☑️ одно из двух опций🤝: <b>оба обязательны</b>. \n\n\n "<b>Установить дату📅</b>" отвечает за установку дня рождения \n\n "<b>Установить уведомление🔔</b>" отвечает за установку уведомления', parse_mode='HTML', reply_markup=await set_notif_date())


async def get_notif(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    await callback.message.answer('уведомления🔔 в формате дд.мм ЧЧ:ММ')
    await state.set_state(BirthdayState.notification_time)


async def set_notif(message: Message, state: FSMContext):
    text = message.text
    try:
        today_date = datetime.datetime.now()
        date_ = datetime.datetime.strptime(text, '%d.%m %H:%M')
        logger.info(f'Before: {date_}')
        date_ = date_.replace(year=today_date.year)
        logger.info(f'After: {date_}')
    except:
        await message.answer('Дату ввели неправильно. Введите дату📅 уведомления🔔 в формате дд.мм ЧЧ:ММ')
        await state.set_state(BirthdayState.notification_time)
        return
    if date_ > today_date:
        date_ = date_.replace(year=today_date.year)

        logger.info("IF enter")
    else:
        date_ = date_.replace(year=today_date.year + 1)
    await state.update_data(notification_time=date_)
        
    data = await state.get_data()
    if 'date' in data:
        await message.answer(f'Введите язык поздравления', reply_markup= await universal_keyboard({'ru': None, 'en': None, 'uz': None}, size=2))
        await state.set_state(BirthdayState.lang)
        return
        # await create_birthday(message=message, data=data, state=state)
    logger.info(f'Notification {data=}')
    await message.answer('Введите дату📅 дня рождения🎂 в формате дд.мм.гггг')
    await state.set_state(BirthdayState.date)


async def get_date(callback: CallbackQuery, state: FSMContext):
    await callback.answer('good job date')
    await callback.message.answer('Введите дату📅 дня рождения🎂 в формате дд.мм.гггг')
    await state.set_state(BirthdayState.date)


async def set_date(message: Message, state: FSMContext):
    text = message.text
    try:
        date_ = datetime.datetime.strptime(text, '%d.%m.%Y')
    except:
        await message.answer('Дату ввели неправильно. Введите дату📅 дня рождения🎂 в формате дд.мм.гггг')
        await state.set_state(BirthdayState.date)
        return
    await state.update_data(date=date_)
    data = await state.get_data()
    if 'notification_time' in data:
        await message.answer(f'Введите язык поздравления', reply_markup= await universal_keyboard(lang_data, size=2))
        await state.set_state(BirthdayState.lang)
        
        return
        # await create_birthday(message=message, data=data, state=state)
    logger.info(f'Date {data=}')
    await message.answer('Введите дату📅 уведомления🔔 в формате дд.мм ЧЧ:ММ')
    await state.set_state(BirthdayState.notification_time)


async def set_lang(message: Message, state: FSMContext):
    try:
        lang = LangSchema(lang=message.text)
        await state.update_data(lang=lang.lang)
        await message.answer(f'Кто он вам?')
        await state.set_state(BirthdayState.desc)
    except:
        await message.answer('Выберите правильный язык из предложенных', reply_markup= await universal_keyboard(lang_data, size=2))
        await state.set_state(BirthdayState.lang)


async def set_desc(message: Message, state: FSMContext):
    await state.update_data(desc=message.text)
    await message.answer(f'Введите время поздравления. Формат: <b>ЧЧ:ММ</b> \nПримеры:\n\n<b>07:10\n22:50</b>', reply_markup=ReplyKeyboardRemove())
    await state.set_state(BirthdayState.time__)


async def set_time(message: Message, state: FSMContext):
    try:
        time__ = TimeSchema(time__=message.text)
        await state.update_data(time__=time__.time__)
        data = await state.get_data()
        await create_birthday(message, data, state)
    except ValidationError:
        await state.set_state(BirthdayState.time__)
        await message.answer(f'Время введено неправильно. Введите время в указанно формате: <b>ЧЧ:ММ</b>')


async def create_birthday(message: Message, data: dict, state: FSMContext):
    full_name = data.get('full_name')
    birthday_boy_id = data.get('birthday_boy_id')
    notification_time = data.get('notification_time')
    lang = data.get('lang')
    desc = data.get('desc')
    time__: datetime.time = data.get("time__")
    date: datetime.datetime = data.get('date')
    date = date.replace(hour=time__.hour, minute=time__.minute) # Setting the time to the current time
    logger.info(f'Notif date: {notification_time} \n {type(notification_time)=}')
    
    birth = insert(Birthdays).values(
        user_id=message.from_user.id,
        full_name=full_name,
        birthday_boy_id=birthday_boy_id,
        notification_time=notification_time,
        date=date,
        desc=desc,
        lang=lang).returning(
            Birthdays.date, Birthdays.birthday_boy_id, Birthdays.birthday_boy_username, Birthdays.full_name, Birthdays.user_id, Birthdays.notification_time, Birthdays.id, Birthdays.lang, Birthdays.desc)
    async with Session() as conn:
        res = await conn.execute(birth)
        await conn.commit()
        n_obj: Birthdays = res.fetchone()
        logger.info(f'{n_obj=} {n_obj.date}')
        try:
            await state.clear()
            await conn.commit()
            await message.answer(f'Добавлено: \nИмя: {n_obj.full_name} \nДата рождения: {n_obj.date.strftime('%d %B, %Y')} \nДата уведомления: {n_obj.notification_time.strftime('%d %B, %Y, %H:%M')}')
            await message.answer('Добавление завершено', reply_markup=start_buttons)
            logger.info(f'Notification set')
        except Exception as e:
            await conn.rollback()
            await bot.send_message(message.from_user.id, f'create_birthday: {e}')
            
        await set_sending_time(notification_time, message.from_user.id, n_obj)
        await congratulate(message, n_obj)


async def congratulate(message: Union[Message, int], imeninnik : Birthdays, bot: Bot = bot):
    imeninnik_name = imeninnik.full_name
    if isinstance(message, Message):
        user = message.from_user.username if message.from_user.username else message.from_user.first_name
        if message.from_user.username is not None:
            text = generate(prompt_with_username.format(imeninnik_name, user, imeninnik.lang, imeninnik.desc))
        else:
            text = generate(prompt_without_username.format(imeninnik_name, user, imeninnik.lang, imeninnik.desc))
    else:
        async with Session() as conn:
            try:
                q = select(User).where(User.id == message)
                res: User = await conn.scalar(q)
                user = res.username if res.username else res.full_name
                if res.username is not None:
                    text = generate(prompt_with_username.format(imeninnik_name, user, imeninnik.lang, imeninnik.desc))
                else:
                    text = generate(prompt_without_username.format(imeninnik_name, user, imeninnik.lang, imeninnik.desc))
            except Exception as e:
                res = select(User).where(User.username == 'Diamondman51')
                admin: User = await conn.scalar(res)
                await bot.send_message(admin.id, f'Exeption: congratulate {e}')

    today = datetime.datetime.now()
    birth_date = imeninnik.date.replace(year=today.year)
    logger.info(f'Congratulate {today < birth_date=}')
    if today < birth_date:
        send_notification.apply_async(args=(message.from_user.id if isinstance(message, Message) else message, text, imeninnik.birthday_boy_id, False), countdown=(birth_date-today).total_seconds())
        logger.info(f'{text=} {(birth_date-today).total_seconds()}')
    else:
        birth_date = imeninnik.date.replace(year=today.year + 1)
        send_notification.apply_async(args=(message.from_user.id if isinstance(message, Message) else message, text, imeninnik.birthday_boy_id, False), countdown=(birth_date-today).total_seconds())
        logger.info(f'Congrat changed to one year forward {(birth_date-today).total_seconds()}')


async def cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Cancelled')
    await callback.message.answer('Отменено', reply_markup=start_buttons)
    await state.clear()


async def cancel_t(message: Message, state: FSMContext):
    await message.answer('Отменено', reply_markup=start_buttons)
    await state.clear()


async def show_birthdays(message: Message):
    user_id = message.from_user.id
    async with Session() as conn:
        birthdays = select(Birthdays).where(Birthdays.user_id == user_id).order_by(Birthdays.date)
        birthdays = await conn.execute(birthdays)
        birthdays = birthdays.scalars().all()
        if not birthdays:
            await message.answer('Вы еще не добавили дни рождения', reply_markup=start_buttons)
            return
        
        # dict_birthdays = {i.full_name: i.birthday_boy_id for i in birthdays}
        await message.answer('Это все ваши добавленные дни рождения🎂✅', reply_markup=start_buttons)
        await message.answer('Ваши дни рождения🎂', reply_markup=await paginator(session=conn, user_id=message.from_user.id))


async def pagination_handler(call: CallbackQuery, callback_data: Pagination):
    page = callback_data.page  # Получение номера страницы из callback data
    async with Session() as session:
        if callback_data.is_group:
            user: User = await get_user(user_id=call.message.from_user.id, session=session)
            groups: Groups = user.groups
            await call.message.edit_reply_markup(reply_markup=await paginator(session=session, page=page, user_id=call.from_user.id, data_seq=groups))  # Обновление клавиатуры при нажатии кнопок "вперед" или "назад"

        await call.message.edit_reply_markup(reply_markup=await paginator(session=session, page=page, user_id=call.from_user.id))  # Обновление клавиатуры при нажатии кнопок "вперед" или "назад"


async def show_birthday(callback: CallbackQuery, callback_data: BirthdayCallback, state: FSMContext, bot: Bot):
    await callback.answer()
    async with Session() as conn:
        birthday = select(Birthdays).where(Birthdays.birthday_boy_id == callback_data.id)
        birthday = await conn.execute(birthday)
        birthday = birthday.scalar()
        try:
            await callback.message.answer(f'Имя: {birthday.full_name}✅ \nДата рождения: {birthday.date.strftime('%d %B, %Y')} \nДата уведомления: {birthday.notification_time.strftime('%d %B, %Y, %H:%M')}🔔', reply_markup=await edit(birthday.birthday_boy_id))
        except Exception as e:
            await callback.message.answer('Именинник возможно удален(')
            res = select(User).where(User.username == 'Diamondman51')
            admin: User = await conn.scalar(res)
            await bot.send_message(admin.id, f'Exeption: show birthday: {e}')


async def set_sending_time(notif_date: datetime.datetime, user_id: int, imeninnik: Birthdays):
    today: datetime.datetime = datetime.datetime.now()
    birthday = imeninnik.date.replace(year=today.year)

    if birthday > notif_date:
        between = notif_date - today
        logger.info(f"{birthday=}, {today=}")
        text = f'День рождение {imeninnik.full_name} через {(birthday - notif_date).days} дней \n{(birthday - notif_date).seconds // 3600} часов\n{(birthday - notif_date).seconds % 3600 // 60} минут'

    elif birthday < notif_date:
        birthday = birthday.replace(year=notif_date.year)
        flag = True
        while flag:
            session = Session()
            if birthday < today:
                birthday = birthday.replace(year=birthday.year + 1)
                logger.info('changed')
                await session.commit()
                await session.close()
            else:
                flag = False
                logger.info(f'{flag=}')

        between = notif_date - today
        logger.info(f"{birthday=}, {today=}, {notif_date=}")

        text = f'День рождение {imeninnik.full_name} через {(birthday - notif_date).days} дней \n{(birthday - notif_date).seconds // 3600} часов\n{(birthday - notif_date).seconds % 3600 // 60} минут'
    logger.info(text)
    res = send_notification.apply_async(args=(user_id, text, imeninnik.birthday_boy_id), countdown=between.total_seconds())
    logger.info(f"{res.id=}")
    logger.info(f"Until: {between.total_seconds() // (3600*24)=}")
    logger.info(f"Until: {between.total_seconds()=}")


async def edit_name(call: CallbackQuery, callback_data: Edit, state: FSMContext):
    await call.answer()
    user_id = callback_data.user_id
    await call.message.answer('Введите новое имя: ')
    await state.clear()
    await state.update_data(user_id=user_id)
    await state.set_state(EditState.name)


async def get_edited_name(message: Message, state: FSMContext, bot: Bot):
    async with Session() as conn:
        try:
            data = await state.get_data()
            user_id = data.get('user_id')
            res = select(Birthdays).where(Birthdays.birthday_boy_id == int(user_id), Birthdays.user_id == message.from_user.id)
            birth: Birthdays = await conn.scalar(res)
            birth.full_name = message.text
            await conn.commit()
            await message.answer('Успешно изменено')
            await show_birthdays(message)

        except Exception as e:
            await conn.rollback()
            res = select(User).where(User.username == 'Diamondman51')
            admin: User = await conn.scalar(res)
            await bot.send_message(admin.id, f'get_edited_name {e}')


async def delete_birth(call: CallbackQuery, callback_data: Edit, bot: Bot):
    await call.answer('Deleted')
    logger.info("Enter")
    birth_id = callback_data.user_id

    async with Session() as conn:
        try:
            res = delete(Birthdays).where(Birthdays.birthday_boy_id == birth_id, Birthdays.user_id == call.from_user.id)
            birth = await conn.execute(res)
            await conn.commit()
            await call.message.delete()
            logger.info('Deleted', birth_id, birth.rowcount, call.from_user.id)
            await call.message.answer('Успешно удалено')

        except Exception as e:
            res = select(User).where(User.username == "Diamondman51")
            admin: User = await conn.scalar(res)
            await bot.send_message(admin.id, f'delete_birth: {e}')


async def edit_birth(call: CallbackQuery, callback_data: Edit, state: FSMContext):
    await call.answer()
    user_id = callback_data.user_id
    await call.message.answer('Введите новую дату в виде 01.11.2025 : ')
    await state.set_data({'user_id': user_id})
    await state.set_state(EditState.birth)


async def get_edited_birth(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(birth=datetime.datetime.strptime(message.text, '%d.%m.%Y'))
    await message.answer(f'Введите время поздравления. Формат: <b>ЧЧ:ММ</b> \nПримеры:\n\n<b>07:10\n22:50</b>', reply_markup=ReplyKeyboardRemove())
    await state.set_state(EditState.time_)



async def get_edited_birth_time(message: Message, state: FSMContext, bot: Bot):
    try:
        time_ = TimeSchema(time__=message.text)
        await state.update_data(time_=time_.time__)
    except ValidationError:
        await state.set_state(BirthdayState.time__)
        await message.answer(f'Время введено неправильно. Введите время в указанном формате: <b>ЧЧ:ММ</b>')
        return
    
    async with Session() as conn:
        try:
            data = await state.get_data()
            user_id = data.get('user_id')
            time_ = data.get('time_')
            birth_time = data.get('birth')
            res = select(Birthdays).where(Birthdays.birthday_boy_id == int(user_id), Birthdays.user_id == message.from_user.id)
            birth: Birthdays = await conn.scalar(res)
            birth.date = datetime.datetime.strptime(f'{birth_time} {time_}', '%d.%m.%Y %H:%M')
            await conn.commit()
            await message.answer('Успешно изменено')
            await congratulate(message=message, imeninnik=birth, bot=bot)
            await show_birthdays(message)
            
        except Exception as e:
            await conn.rollback()
            res = select(User).where(User.username == 'Diamondman51')
            admin: User = await conn.scalar(res)
            await bot.send_message(admin.id, f'get_edited_birth: {e}')


async def edit_notif(call: CallbackQuery, callback_data: Edit, state: FSMContext):
    await call.answer()
    user_id = callback_data.user_id
    await call.message.answer('Введите новую дату в виде 01.11 15:38')
    await state.set_data({'user_id': user_id})
    await state.set_state(EditState.notif)


async def get_edited_notif(message: Message, state: FSMContext, bot: Bot):
    async with Session() as conn:
        try:
            data = await state.get_data()
            user_id = data.get('user_id')
            res = select(Birthdays).where(Birthdays.birthday_boy_id == int(user_id), Birthdays.user_id == message.from_user.id)
            birth: Birthdays = await conn.scalar(res)
            birth.notification_time = datetime.datetime.strptime(message.text, '%d.%m %H:%M')
            await conn.commit()
            await message.answer('Успешно изменено')
            await set_sending_time(user_id=user_id, notif_date=birth.notification_time, imeninnik=birth)
            await show_birthdays(message)

        except Exception as e:
            await conn.rollback()
            res = select(User).where(User.username == 'Diamondman51')
            admin: User = await conn.scalar(res)
            await bot.send_message(admin.id, f'get_edited_notif: {e}')


async def get_queue(client_id):
    logger.info('Enter to queue')
    while True:
        logger.info(f'{queue.empty(client_id)=}')
        logger.info(f'{queue._instance=}')
        if not queue.empty(client_id):
            data: dict = queue.get(client_id)
            if data is not None:
                user_id = data.get('user_id')
                imeninnik_id = data.get('imeninnik_id')
                is_notif = data.get('is_notif')
                async with Session() as conn:
                    try:
                        year = datetime.datetime.now()
                        query = select(Birthdays).where(Birthdays.birthday_boy_id == imeninnik_id, Birthdays.user_id == user_id)
                        birth: Birthdays = await conn.scalar(query)
                        if is_notif:
                            birth.notification_time = birth.notification_time.replace(year=year.year + 1)
                            await set_sending_time(birth.notification_time, user_id, birth)
                        else:
                            await congratulate(client_id, birth)
                        await conn.commit()
                        logger.info('reset')
                    except Exception as e:
                        await conn.rollback()
        else:
            logger.info('Waiting 10 seconds')
            await asyncio.sleep(10)





# if __name__ == '__main__':
#     queue = MyQueue.get_instance()
#     asyncio.create_task(get_queue())