import logging
from logging import Logger

def setup_logger(name: str, level: int = logging.INFO, log_file: str = "app.log") -> Logger:
    """
    Sets up a logger with a stream handler (console) and file handler.

    Args:
        name (str): Name of the logger.
        level (int): Logging level (from logging module).
        log_file (str): Path to the log file.

    Returns:
        logging.Logger: A configured logger object.
    """
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(process)d - %(message)s")

    # Stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding multiple handlers if they already exist
    if not logger.handlers:
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger
