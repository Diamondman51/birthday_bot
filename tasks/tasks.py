import asyncio
from functools import wraps
import logging
import os
from aiogram import Bot
from celery import Celery
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.queues import MyQueue
from models.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.exceptions import TelegramBadRequest
import logging


logger = logging.getLogger('bot_celery')

queue = MyQueue()

import config.config as config

engine = create_async_engine("sqlite+aiosqlite:///bot.db")

Session = async_sessionmaker(engine, expire_on_commit=False)

bot = Bot(token=config.BOT_TOKEN)

app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

cache = Redis(host=os.getenv('redis_url'), port=6379, db=1)
cache.flushall()

logger.info('Celery is ready')

@app.task
def send_notification(user_id: int, text: str, imeninnik_id: int, is_notif=True) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(send_async_notification(user_id, text, imeninnik_id, is_notif))
    finally:
        loop.close()
        

async def send_async_notification(user_id: int, text: str, imeninnik_id: int, is_notif=True):
    try:
        logger.info('Enter to try')
        await bot.send_message(user_id, 'Привет!')
        await bot.send_message(user_id, text)
        logger.info('Before send_to_groups')
        await send_to_groups(user_id=user_id, imeninnik_id=imeninnik_id, bot=bot, text=text)
        logger.info('After send_to_groups')
        logger.info(f'Notification sent to {user_id}')
    except Exception as e:
        logger.error(f"Error sending to user {user_id}: {e}")
    finally:
        await bot.session.close()
        queue.put({'user_id': user_id, 'imeninnik_id': imeninnik_id, 'is_notif': is_notif}, name=user_id)


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
    q = select(User).options(selectinload(User.groups)).where(User.id == user_id)
    res = await session.execute(q)
    user: User = res.scalar()
    logger.info('Success')
    return user


async def send_to_groups(user_id, imeninnik_id, bot: Bot, text: str):
    try:
        logger.info(f'Enter to send to groups')
        user: User = await get_user(user_id=user_id)
        group_ids: list[int] = [group.group_id for group in user.groups]
        imen_in_chats = []
        logger.info(f'Group ids: {group_ids}')
        if group_ids:
            for group_id in group_ids:
                try:
                    logger.info(f'Participant(imeninnik) id: {imeninnik_id}')
                    res = await bot.get_chat_member(group_id, imeninnik_id) # TODO
                    logger.info(f'Result of requesting member: {res} \n From group {group_id}')
                    if res.status != 'left':
                        imen_in_chats.append(group_id)
                except TelegramBadRequest as e:
                    logger.info(f'Error while getting member: {e}')

            logger.info(f'imen in chats: {imen_in_chats}')                    
            for group in imen_in_chats:
                await bot.send_message(group, text)
                logger.info(f'Message is sent to the group: {group}')
    except Exception as e:
        logger.error(f'Error from tasks send_to_groups: {e}')

