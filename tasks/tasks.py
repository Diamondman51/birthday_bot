import asyncio
from functools import wraps
import logging
from aiogram import Bot
from celery import Celery
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.queues import MyQueue
from models.models import User
from sqlalchemy.ext.asyncio import AsyncSession

queue = MyQueue()

import config.config as config

engine = create_async_engine("sqlite+aiosqlite:///bot.db")

Session = async_sessionmaker(engine, expire_on_commit=False)

bot = Bot(token=config.BOT_TOKEN)

app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

cache = Redis(host='localhost', port=6379, db=1)
cache.flushall()
logger = logging.getLogger(__name__)


@app.task
def send_notification(user_id: int, text: str, imeninnik_id: int, is_notif=True) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(send_async_notification(user_id, text, imeninnik_id, is_notif))
    finally:
        loop.close()
        

async def send_async_notification(user_id: int, text: str, imeninnik_id: int, is_notif=True):
    await bot.send_message(user_id, 'Привет!')
    await bot.send_message(user_id, text)
    await bot.session.close()
    print(f'from task: {queue._instance}')
    queue.put({'user_id': user_id, 'imeninnik_id': imeninnik_id, 'is_notif': is_notif}, name=user_id)


def get_connection(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with Session.begin() as session:
            # if kwargs.get('session', None):
            kwargs['session'] = session
            return await func(*args, **kwargs)
    return wrapper

async def get_user(user_id: int, session: AsyncSession) -> User:
    q = select(User).options(selectinload(User.birthdays)).where(User.id == user_id)
    res = await session.execute(q)
    user: User = res.scalar()
    logger.info('Success')
    return user


async def send_to_groups(user_id, imeninnik_id):
    user: User = get_user(user_id=user_id)
    group_ids: list[int] = [group.id for group in user.groups]
    for id in group_ids:
        res = await bot.get_chat_member(id, imeninnik_id) # TODO


# async def get_user(user_id: int) -> User:
#     async with Session.begin() as session:
#         q = select(User).options(selectinload(User.birthdays)).where(User.id == user_id)
#         res = await session.execute(q)
#         user: User = res.scalar()
#         return user




# t1 = datetime.datetime(2000, 12, 12)
# t2 = datetime.datetime(2025, 4, 12)
# t3 = datetime.timedelta(days=1)
# print((t1 - t3).day)