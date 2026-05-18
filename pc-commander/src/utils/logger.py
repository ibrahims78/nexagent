import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from src.utils.config import get_logs_dir


def get_logger(name: str = "NexAgent") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logs_dir = get_logs_dir()
        log_file = logs_dir / "commander.log"

        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        file_handler = TimedRotatingFileHandler(
            log_file,
            when="midnight",
            backupCount=30,
            encoding="utf-8",
        )
        file_handler.suffix = "%Y%m%d"
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        logger.setLevel(logging.INFO)

    return logger


def log_command(user_id: int, username: str, command: str, result: str):
    logger = get_logger()
    logs_dir = get_logs_dir()
    commands_log = logs_dir / "commands.log"
    entry = (
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"USER:{user_id}(@{username}) CMD:{command[:100]} RESULT:{result[:200]}\n"
    )
    with open(commands_log, "a", encoding="utf-8") as f:
        f.write(entry)
    logger.info(f"Command from {username}: {command[:100]}")
