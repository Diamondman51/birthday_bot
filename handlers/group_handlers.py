from functools import wraps
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.handlers import Session
from buttons.buttons import EditGroupCallBack, GroupCallBack, edit_group, paginator
from models.models import Groups, User

logger = logging.getLogger(__name__)


async def connection():
    async with Session.begin() as session:
        return session


def get_connection(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with Session.begin() as session:
            # if kwargs.get('session', None):
            kwargs['session'] = session
            return await func(*args, **kwargs)
    return wrapper


@get_connection
async def get_user(user_id: int, session: AsyncSession) -> User:
    q = select(User).options(selectinload(User.birthdays), selectinload(User.groups)).where(User.id == user_id)
    res = await session.execute(q)
    user: User = res.scalar()
    logger.info('Success')
    return user


async def user_has_group(group_id, user: User) -> bool:
    user_groups = [group.group_id for group in user.groups]
    return group_id in user_groups


async def get_group_id(message: Message, bot: Bot):
    try:
        chat = await bot.get_chat(message.chat_shared.chat_id)
        # await bot.send_message(-1002795984024, 'hello')
        logger.info(chat.title)
        user: User = await get_user(user_id=message.from_user.id)
        name = chat.title
        group_id = chat.id
        session = Session()

        res = await user_has_group(group_id=group_id, user=user)
        if not res:
            group = Groups(name=name, group_id=group_id, user=user)
            session.add(group)
            await session.commit()
            await session.close()
        else:
            await message.answer('Группа уже добавлена')
            return
        await message.answer(f'''
        {user=}\n{group_id=}\n{name=}\n''')
    except TelegramBadRequest as e:
        match e.message:
            case 'Bad Request: chat not found':
                await message.answer(f'Сначала <b>добавьте бота</b> в выбранную группу, затем попробуйте снова. Error: {e.message}')    
            case 'Bad Request: member not found':
                pass
    except Exception as e:
        await message.answer('Internal error')
        logger.error(f'{e}')
    await session.close()

    # await message.answer(f'{}')


async def show_groups(message: Message, state: FSMContext):
    user: User = await get_user(message.from_user.id)
    groups = user.groups
    session = await connection()
    await message.answer('Группы:', reply_markup=await paginator(session=session, data_seq=groups, user_id=message.from_user.id))


async def get_group_callback(call: CallbackQuery, callback_data: GroupCallBack):
    await call.answer('Хорошо господин')
    group_id = callback_data.group_id
    user_id = call.from_user.id
    session = await connection()
    q = select(Groups).where(Groups.group_id == group_id, Groups.user_id == user_id)
    res = await session.execute(q)
    group: Groups = res.scalar_one_or_none()
    await session.close()
    await call.message.answer(f'Название группы: 👥 <b>{group.name}</b>', reply_markup=await edit_group(user_id=user_id, group_id=group_id))


async def group_edit_action(call: CallbackQuery, callback_data: EditGroupCallBack):
    await call.answer('Принял ваши приказы мой господин')
    if callback_data.action == 'delete':
        session = await connection()
        q = delete(Groups).where(Groups.user_id==call.from_user.id, Groups.group_id==callback_data.group_id).returning(Groups.name)
        res = await session.execute(q)
        group_name = res.scalar_one_or_none()
        await session.commit()
        await call.message.answer(f'Группа удалена: {group_name}')
        await call.message.delete()
        await session.close()
    elif callback_data.action == 'cancel':
        await call.message.delete()

