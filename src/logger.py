import datetime
import logging
import os

class ContextLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return f"{msg}", {**kwargs, 'extra': self.extra}


class CustomLogger:
    def __init__(self, class_name, function_name, logger_name='NvidiaCollector'):
        if not os.path.exists('logs'):
            os.makedirs('logs')

        log_file = f"logs/nvidia_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = False  # evita imprimir en consola

        if not logger.handlers:
            file_handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '[%(asctime)s | %(name)s | %(class_name)s | %(function_name)s | %(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        self.logger = ContextLogger(logger, {
            'class_name': class_name,
            'function_name': function_name
        })

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message, exc_info=False):
        self.logger.error(message, exc_info=exc_info)

