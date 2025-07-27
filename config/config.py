import logging
import os

import betterlogging
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
def setup_logging():
    log_level = logging.INFO
    betterlogging.basic_colorized_config(level=log_level)
    logger = logging.getLogger(__name__)
    logger.info(f'\nLogging set up')
