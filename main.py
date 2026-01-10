#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GD音乐播放器 - 主程序入口
功能：搜索、播放、收藏、下载音乐
"""

import tkinter as tk
import sys
import os
import traceback

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def init_application():
    """初始化应用程序"""
    try:
        from utils.file_handler import FileHandler
        
        print("=" * 50)
        print("GD音乐播放器 启动初始化")
        print("=" * 50)
        
        # 初始化所有必要的目录和文件
        data_dir = FileHandler.get_data_dir()
        download_dir = FileHandler.get_download_dir()
        
        print(f"数据目录: {data_dir}")
        print(f"下载目录: {download_dir}")
        
        # 预加载必要的数据文件（如果不存在会自动创建）
        FileHandler.load_favorites()
        FileHandler.load_playlist()
        FileHandler.load_download_history()
        
        print("初始化完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"[启动错误] 初始化失败: {e}")
        traceback.print_exc()

def main():
    """主函数"""
    # 初始化应用
    init_application()
    
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
        
        # 启动主循环
        root.mainloop()
        
    except Exception as e:
        print(f"程序启动失败: {e}")
        traceback.print_exc()
        input("按Enter键退出...")

if __name__ == "__main__":
    main()