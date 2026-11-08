import logging
import os

def setup_logger(log_file="app.log", log_level=logging.INFO):
    """配置全局日志器"""
    logger = logging.getLogger("EBFR")  # 指定统一的 logger 名字
    logger.setLevel(log_level)

    # 避免重复添加 handler
    if not logger.handlers:
        # 创建日志目录
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 文件输出
        file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
        file_handler.setLevel(log_level)

        # 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        # 日志格式
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加 handler
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger