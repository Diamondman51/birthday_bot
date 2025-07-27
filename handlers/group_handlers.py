from functools import wraps
import logging
from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.handlers import Session
from models.models import Birthdays, User

logger = logging.getLogger(__name__)

def get_connection(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with Session.begin() as session:
            print(args, '-------------------------------------------------------------')
            # if kwargs.get('session', None):
            kwargs['session'] = session
            return await func(*args, **kwargs)
    return wrapper

@get_connection
async def get_users_birthday_list(user_id: int, session: AsyncSession) -> list[Birthdays]:
    print('Lollllll---------------------------------------------------------')
    q = select(User).options(selectinload(User.birthdays)).where(User.id == user_id)
    res = await session.execute(q)
    user: User = res.scalar()
    logger.info('Success')
    birthday_list = user.birthdays
    return birthday_list


async def get_group_id(message: Message, state: FSMContext, bot: Bot):
    birthdays: list[Birthdays] = await get_users_birthday_list(message.from_user.id)
    # logger.info(f'Birthday list: {birthdays}')
    await message.answer(f'{birthdays}')
    await state.update_data(group_id=message.chat_shared.chat_id)
    
