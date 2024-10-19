"""Модуль содержащий в себе методы логирования."""
import logging
import os
from logging.handlers import RotatingFileHandler

from ..configs.settings import log_lvl

LOG_FORMAT = '%(asctime)s,%(msecs)d %(levelname)-8s [%(module)s:%(lineno)d in %(funcName)s] %(message)s'
MAX_BYTES = 10 * 1024 * 1024


class Logger:
    """Класс для логирования."""

    logger = logging.getLogger(__name__)

    def __init__(self, log_name: str, level: int):
        """
        Метод инициализации класса для логирования.

        :param log_name: В какой файл писать. Если запуск установлен из main.py -> log_name=='Main'
        :param level: Установить уровень логирования
        """
        self.log_dir = 'logs/{}/{}.log'.format(log_name, log_name)
        self.log_format = LOG_FORMAT
        self.log_datefmt = '%d-%m-%Y %H:%M:%S'
        self.handler = RotatingFileHandler(self.log_dir, maxBytes=MAX_BYTES, encoding='utf-8', delay=False, backupCount=1)

        logging.basicConfig(format=self.log_format, datefmt=self.log_datefmt, level=level, handlers=[self.handler])


def selector_logger(module_logger: str, level: int = log_lvl):
    """
    Селектор для логера

    :param module_logger: Имя файла с точкой входа для логирования
    :param level: уровень логирования
    return Класс логера
    """
    logs_path = os.path.join('logs', module_logger)
    if not os.path.exists(logs_path):
        os.makedirs(logs_path, exist_ok=True)

    if not os.path.isdir(logs_path):
        raise FileExistsError(f'Файл {logs_path} не является каталогом')
    return Logger(module_logger, level).logger
