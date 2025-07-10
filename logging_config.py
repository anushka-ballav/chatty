import logging
import sys
from loguru import logger as loguru_logger
from config import settings

class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
            
        loguru_logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging():
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    loguru_logger.configure(
        handlers=[
            {
                "sink": sys.stdout, 
                "level": settings.LOG_LEVEL.upper(),
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                "colorize": True,
            },
            {
                "sink": "logs/app.log",
                "level": settings.LOG_LEVEL.upper(),
                "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
                "rotation": "10 MB",
                "compression": "zip",
                "serialize": False,
            }
        ]
    )
