# gui/base_panel.py
import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod

class BasePanel(ABC):
    """基础面板类"""
    
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app  # 主程序引用
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        
    @abstractmethod
    def setup_ui(self):
        """设置UI界面"""
        pass
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        if hasattr(self.main_app, 'logger'):
            self.main_app.logger.log(message, level)
        else:
            print(f"[{level}] {message}")
    
    def show_message(self, title: str, message: str, type: str = "info"):
        """显示消息对话框"""
        if type == "info":
            messagebox.showinfo(title, message)
        elif type == "warning":
            messagebox.showwarning(title, message)
        elif type == "error":
            messagebox.showerror(title, message)
        elif type == "ask":
            return messagebox.askyesno(title, message)
        return None