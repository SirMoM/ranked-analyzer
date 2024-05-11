import dataclasses
import json
import logging
import os
import string
from datetime import datetime


def setup_default_logger():
    # Create logs directory if it doesn't exist
    if not os.path.exists("./logs"):
        os.makedirs("./logs")

    log_format = logging.Formatter(
        "%(asctime)s - [%(levelname)s] %(message)s", "%H:%M:%S"
    )

    # Console handler setup
    _console_handler = logging.StreamHandler()
    _console_handler.setLevel(logging.INFO)
    _console_handler.setFormatter(log_format)

    # File handler setup
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file = f"./logs/{current_date}.log"
    _file_handler = logging.FileHandler(log_file)
    _file_handler.setLevel(logging.DEBUG)
    _file_handler.setFormatter(log_format)

    return _console_handler, _file_handler


console_handler, file_handler = setup_default_logger()


def get_logger(name):
    root = logging.getLogger()
    root.addHandler(console_handler)
    root.addHandler(file_handler)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    return logger


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, datetime):
            return o.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            return super().default(o)
        finally:
            # Catch all objects that cannot be serialized and just return their string
            return str(o)


def stringify(datacls) -> string:
    return json.dumps(datacls, cls=EnhancedJSONEncoder, indent=2)
