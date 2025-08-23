from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Request
from aiogram.types import Update
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
import config.config as config
import app.router as router
from dotenv import load_dotenv

load_dotenv()

PORT = 8000


storage = MemoryStorage()

dp = Dispatcher(
    storage=storage,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Bot is starting')
    config.setup_logging()
    await delete_webhook()
    await set_webhook()
    yield
    await delete_webhook()
    print('Bot is stopped')

app = FastAPI(lifespan=lifespan)

bot = Bot(
    token=config.BOT_TOKEN,
    # session=session,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)


HOOK = '/hook/'
# URL = input('Enter ngrok url: ')
URL = os.getenv('url')
HOOK_URL = f'{URL}{HOOK}'
# HOOK_URL = f'https://318c-104-154-169-9.ngrok-free.app/bot{HOOK}'

dp.include_router(router.setup())

@app.get("/set_hook")
async def set_webhook():
    await bot.set_webhook(HOOK_URL)
    return {'web_hook': 'True'}

@app.get("/delete_hook")
async def delete_webhook():
    await bot.delete_webhook(drop_pending_updates=True)
    return {'web_hook': 'False'}

@app.post(HOOK)
async def get_update(request: Request):
    data = await request.json()
    # print(data)
    update = Update(**data)
    await dp.feed_update(bot=bot, update=update)
    return {'update': 'True'}


# def base64_to_image(base64_string: str) -&gt; np.ndarray:
#     image = base64.b64decode(base64_string.split(',')[1])
#     image = np.frombuffer(image, np.uint8)
#     image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)
#     return image