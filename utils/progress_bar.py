import sys
import time

class ProgressBar:
    def __init__(self, total: int = 100, prefix: str = '', suffix: str = '', decimals: int = 1, 
                 length: int = 50, fill: str = '█', print_end: str = "\r"):
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.length = length
        self.fill = fill
        self.print_end = print_end
        self.current = 0
        self.start_time = time.time()

    def print_progress(self, iteration: int):
        """打印进度条"""
        self.current = iteration
        percent = ("{0:." + str(self.decimals) + "f}").format(100 * (iteration / float(self.total)))
        filled_length = int(self.length * iteration // self.total)
        bar = self.fill * filled_length + '-' * (self.length - filled_length)
        
        # 计算剩余时间
        elapsed_time = time.time() - self.start_time
        if iteration > 0:
            eta = elapsed_time * (self.total / iteration - 1)
            time_info = f" | ETA: {self._format_time(eta)}"
        else:
            time_info = ""
        
        sys.stdout.write(f'\r{self.prefix} |{bar}| {percent}% {self.suffix}{time_info}')
        sys.stdout.flush()
        
        if iteration == self.total:
            total_time = time.time() - self.start_time
            sys.stdout.write(f'\n完成! 总用时: {self._format_time(total_time)}\n')

    def _format_time(self, seconds: float) -> str:
        """格式化时间"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{int(hours)}h {int(minutes)}m" 