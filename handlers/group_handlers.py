from functools import wraps
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.handlers import Session
from models.models import Groups, User

logger = logging.getLogger(__name__)

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
    q = select(User).options(selectinload(User.birthdays)).where(User.id == user_id)
    res = await session.execute(q)
    user: User = res.scalar()
    logger.info('Success')
    return user


async def get_group_id(message: Message, state: FSMContext, bot: Bot):
    try:
        chat = await bot.get_chat(message.chat_shared.chat_id)
        logger.info(chat.title)
        user: User = await get_user(message.from_user.id)
        name = chat.title
        group_id = chat.id
        q = select(exists().where(Groups.group_id == group_id))
        # user.groups.append(group)
        session = Session()
        res = await session.execute(q)
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
    except TelegramBadRequest:
        await message.answer(f'Сначала <b>добавьте бота</b> в выбранную группу, затем попробуйте снова.')    
    except Exception as e:
        await message.answer('Internal error')
        logger.error(f'{e}')

    # await message.answer(f'{}')

    
