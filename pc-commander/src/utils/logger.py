import logging
from datetime import datetime
from src.utils.config import get_logs_dir

_logger = None


def get_logger(name="NexAgent") -> logging.Logger:
    global _logger
    if _logger:
        return _logger

    logs_dir = get_logs_dir()
    log_file = logs_dir / f"commander_{datetime.now().strftime('%Y%m%d')}.log"

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    _logger = logger
    return logger


def log_command(user_id: int, username: str, command: str, result: str):
    logger = get_logger()
    logs_dir = get_logs_dir()
    commands_log = logs_dir / "commands.log"
    entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] USER:{user_id}(@{username}) CMD:{command[:100]} RESULT:{result[:200]}\n"
    with open(commands_log, "a", encoding="utf-8") as f:
        f.write(entry)
    logger.info(f"Command from {username}: {command[:100]}")
