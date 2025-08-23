from aiogram.types import KeyboardButton, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButtonRequestUser, KeyboardButtonPollType, KeyboardButtonRequestChat
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from sqlalchemy.ext.asyncio import AsyncSession  # Импорт AsyncSession для работы с базой данных
from sqlalchemy import select
from models.models import Birthdays, Groups


start = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text="Добавить день рождение"), KeyboardButton(text="Показать дни раждения")
    ], 
    [
        KeyboardButton(text="Добавить группу", request_chat=KeyboardButtonRequestChat(request_id=1, chat_is_channel=False)),
        KeyboardButton(text="Показать группы")
    ]
    ], resize_keyboard=True, one_time_keyboard=True)


async def get_username_id():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Отправить id именинника", request_user=KeyboardButtonRequestUser(request_id=1)), KeyboardButton(text='Отмена'))
    return builder.as_markup(resize_keyboard=True)


async def select_allusers(session: AsyncSession, user_id):
    query = select(Birthdays).where(Birthdays.user_id == user_id)  # Предположим, что ваша модель пользователей называется "User"
    result = await session.execute(query)  # Выполнение запроса к базе данных
    users = result.scalars().all()  # Получение списка пользователей
    return users  # Возвращение списка пользователей


async def set_notif_date():
    builder = InlineKeyboardBuilder()
    builder.button(text="Установить дату", callback_data="set_date")
    builder.button(text="Установить уведомление", callback_data="set_notif")
    builder.button(text="Отменить", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


class Pagination(CallbackData, prefix="pag"):
    action: str  # Действие
    page: int  # Номер страницы
    is_group: bool
    

# Функция для создания клавиатуры с пользователями и кнопками для перелистывания
async def paginator(session: AsyncSession, data_seq =    None, page: int = 0, limit: int = 5, user_id=0):
    if data_seq:
        data: Groups = data_seq
    else:
        data = await select_allusers(session=session, user_id=user_id)  # Получение списка пользователей
    
    builder = InlineKeyboardBuilder()  # Создание объекта InlineKeyboardBuilder
    start_offset = page * limit  # Вычисление начального смещения на основе номера страницы
    end_offset = start_offset + limit  # Вычисление конечного смещения

    if not data_seq:
        for user in data[start_offset:end_offset]:  # Перебор пользователей для текущей страницы
            builder.row(InlineKeyboardButton(text=f'👤 {user.full_name}', callback_data=BirthdayCallback(action='get', id=user.birthday_boy_id).pack()))  # Добавление кнопки для каждого пользователя
    else:
        for group in data[start_offset:end_offset]:  # Перебор пользователей для текущей страницы
            group: Groups = group
            builder.row(InlineKeyboardButton(text=f'👥 {group.name}', callback_data=GroupCallBack(group_id=group.group_id, user_id=group.user_id).pack()))  # Добавление кнопки для каждого пользователя



    buttons_row = []  # Создание списка кнопок
    if page > 0:  # Проверка, что страница не первая
        buttons_row.append(InlineKeyboardButton(text="⬅️", callback_data=Pagination(action="prev", page=page - 1, is_group=False if data_seq is None else True).pack()))  # Добавление кнопки "назад"
    if end_offset < len(data):  # Проверка, что ещё есть пользователи для следующей страницы
        buttons_row.append(InlineKeyboardButton(text="➡️", callback_data=Pagination(action="next", page=page + 1, is_group=False if data_seq is None else True).pack()))  # Добавление кнопки "вперед"
    elif limit < len(data):  # Если пользователи закончились
        buttons_row.append(InlineKeyboardButton(text="➡️", callback_data=Pagination(action="next", page=0, is_group=False if data_seq is None else True).pack()))  # Возвращение на первую страницу
    builder.row(*buttons_row)  # Добавление кнопок навигации
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='cancel'))  # Добавление кнопки "назад"
    await session.close()
    return builder.as_markup()  # Возвращение клавиатуры в виде разметки


class Edit(CallbackData, prefix='edit'):
    action: str
    user_id: int


class GroupCallBack(CallbackData, prefix='group'):
    user_id: int
    group_id: int


class EditGroupCallBack(CallbackData, prefix='edit_group'):
    user_id: int
    group_id: int
    action: str


async def edit(user_id):
    button = InlineKeyboardBuilder()
    button.add(InlineKeyboardButton(text='Изменить имя', callback_data=Edit(action='edit_name', user_id=user_id).pack()))
    button.row(InlineKeyboardButton(text='Изменить дату рождения', callback_data=Edit(action='edit_birth', user_id=user_id).pack()), 
               InlineKeyboardButton(text="Изменить дату уведомления", callback_data=Edit(action='edit_notif', user_id=user_id).pack()))
    button.row(InlineKeyboardButton(text='Удалить', callback_data=Edit(action='delete', user_id=user_id).pack()))
    return button.as_markup()


async def edit_group(user_id, group_id):
    button = InlineKeyboardBuilder()
    button.row(InlineKeyboardButton(text='Назад', callback_data=EditGroupCallBack(action='cancel', user_id=user_id, group_id=group_id).pack()), 
               InlineKeyboardButton(text='Удалить', callback_data=EditGroupCallBack(action='delete', user_id=user_id, group_id=group_id).pack()))
    return button.as_markup()


async def universal_keyboard(buttons: dict=None, size: int = None):
    '''
    request_users
    request_chat
    request_contact
    request_location
    request_poll
    '''
    if buttons is None:
        return 0
    
    builder = ReplyKeyboardBuilder()

    for button, property in buttons.items():
        match property:
            case 'request_users':
                builder.button(text=button, request_user=KeyboardButtonRequestUser(request_id=1))
            case 'request_chat':
                builder.button(text=button, request_chat=KeyboardButtonRequestChat(request_id=1))

            case 'request_contact':
                builder.button(text=button, request_contact=True)

            case 'request_location':
                builder.button(text=button, request_location=True)

            case 'request_poll':
                builder.button(text=button, request_poll=KeyboardButtonPollType(type='regular'))
        builder.button(text=button)
    if size:
        builder.adjust(size)
        return builder.as_markup(resize_keyboard=True)
    return builder.as_markup(resize_keyboard=True)


class BirthdayCallback(CallbackData, prefix='birthday'):
    action: str
    id: int

lang_data = {'ru': None, 'en': None, 'uz': None}
