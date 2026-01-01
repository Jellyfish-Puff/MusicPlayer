from datetime import datetime
import tkinter as tk
from typing import Optional

class Logger:
    """日志记录器"""
    
    def __init__(self, text_widget: Optional[tk.Text] = None):
        self.text_widget = text_widget
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}\n"
        
        # 输出到控制台
        print(log_message.strip())
        
        # 输出到GUI（如果有）
        if self.text_widget:
            self.text_widget.insert(tk.END, log_message)
            self.text_widget.see(tk.END)
            self.text_widget.update()