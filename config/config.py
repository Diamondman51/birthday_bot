import logging
import os

import betterlogging
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')


def setup_logging():
    # logging.basicConfig(
    #     level=logging.INFO,
    #     format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    #     datefmt="%Y-%m-%d %H:%M:%S",
    #     handlers=[
    #         logging.FileHandler("bot.log", encoding='utf-8'),
    #         logging.StreamHandler()  # Optional: also print to console
    #     ]
    # )
    log_level = logging.INFO
    betterlogging.basic_colorized_config(level=log_level)
    logger = logging.getLogger(__name__)
    logger.info(f'\nLogging set up')
