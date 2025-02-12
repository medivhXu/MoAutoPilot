import logging
import os
import time

class Logger:
    def __init__(self):
        # 创建logger
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        # 创建handler
        log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_path, exist_ok=True)  # 确保日志目录存在
        
        log_name = os.path.join(log_path, f'{time.strftime("%Y%m%d")}.log')
        fh = logging.FileHandler(log_name, encoding='utf-8')
        ch = logging.StreamHandler()

        # 设置输出格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # 添加handler
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def get_logger(self):
        return self.logger 