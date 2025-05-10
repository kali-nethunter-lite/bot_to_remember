import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot_logs.txt", encoding="utf-8"),
        logging.StreamHandler()
    ])
logger = logging.getLogger(__name__)
