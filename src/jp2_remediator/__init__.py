import logging
from logging.handlers import TimedRotatingFileHandler
import os
import socket
from datetime import datetime

LOG_FILE_BACKUP_COUNT = int(os.getenv('LOG_FILE_BACKUP_COUNT', '30'))
LOG_ROTATION = "midnight"

timestamp = datetime.today().strftime('%Y-%m-%d')


def configure_logger(name):  # pragma: no cover
    log_level = os.getenv("APP_LOG_LEVEL", "WARNING")
    log_dir = os.getenv("LOG_DIR", "logs/")
    # create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file_path = os.path.join(log_dir, "jp2_remediator.log")
    formatter = logging.Formatter(
        '%(levelname)s - %(asctime)s - %(name)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(console_handler)
    # Defaults to console logging
    if os.getenv("CONSOLE_LOGGING_ONLY", "true") == "false":
        # make log_file_path if it doesn't exist
        # os.makedirs(log_file_path, exist_ok=True)
        file_handler = TimedRotatingFileHandler(
            filename=log_file_path,
            when=LOG_ROTATION,
            backupCount=LOG_FILE_BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.setLevel(log_level)
    return logger
