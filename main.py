#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GD音乐播放器 - 主程序入口
功能：搜索、播放、收藏、下载音乐
"""

import tkinter as tk
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """主函数"""
    try:
        # 检查依赖
        import requests
        import pygame
        from PIL import Image, ImageTk
        
    except ImportError as e:
        print(f"缺少必要的依赖库: {e}")
        print("请安装以下库:")
        print("pip install requests pygame pillow")
        input("按Enter键退出...")
        return
    
    # 创建主窗口
    root = tk.Tk()
    
    # 导入主窗口类
    from gui.main_window import MainWindow
    
    try:
        # 创建应用程序
        app = MainWindow(root)
        
        # 配置窗口
        root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, app))
        
        # 启动主循环
        root.mainloop()
        
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按Enter键退出...")

def on_closing(root, app):
    """处理窗口关闭事件"""
    # 保存收藏
    if hasattr(app, 'save_favorites'):
        app.save_favorites()
    
    # 停止播放
    if hasattr(app, 'player_window') and app.player_window:
        app.player_window.stop()
    
    # 关闭窗口
    root.destroy()

if __name__ == "__main__":
    main()