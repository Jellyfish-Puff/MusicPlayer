import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import threading
import os
import time
from datetime import datetime

from api.music_api import MusicAPI
from utils.file_handler import FileHandler
from utils.logger import Logger
from gui.player_window import PlayerWindow

class MainWindow:
    """主窗口"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("GD音乐播放器")
        self.root.geometry("1200x800")
        
        # 初始化组件
        self.api = MusicAPI()
        self.file_handler = FileHandler()
        self.logger = Logger()
        self.player_window = None
        
        # 数据 - 在 setup_ui 之前先初始化所有属性
        self.favorites = []
        self.current_playlist = []
        self.song_data_cache = {}  # 缓存歌曲数据，键为item_id
        
        # 下载相关属性
        self.download_dialog = None
        self.download_progress_var = None
        self.download_progress_bar = None
        self.download_status_label = None
        self.download_speed_label = None
        self.download_cancel_button = None
        self.download_start_time = None
        self.last_downloaded = 0
        self.last_time = None
        self.is_download_cancelled = False
        self.download_progress_data = {'last_update': 0, 'progress': 0}
        
        # 初始化UI控件引用（避免属性错误）
        self.results_tree = None
        self.fav_tree = None
        self.fav_stats_label = None
        self.tab_control = None
        self.search_entry = None
        self.search_type = None
        self.quality_combo = None
        self.log_text = None
        self.info_text = None
        self.fav_search_entry = None
        self.playlist_listbox = None
        self.download_tree = None
        self.download_path_var = None
        
        # 创建界面
        self.setup_ui()
        
        # 加载收藏数据
        self.load_favorites()
    
    def setup_ui(self):
        """设置主界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建左侧面板（搜索和结果）
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 创建右侧面板（选项卡）
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        
        # 设置左侧面板
        self._setup_left_panel(left_panel)
        
        # 设置右侧面板（改为选项卡）
        self._setup_right_tab_panel(right_panel)
    
    def _setup_left_panel(self, parent):
        """设置左侧面板（搜索部分）"""
        # 搜索部分
        search_frame = ttk.LabelFrame(parent, text="搜索音乐", padding="10")
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(search_frame, text="音乐源:").grid(row=0, column=0, sticky=tk.W)
        self.search_type = ttk.Combobox(search_frame, values=["netease", "kuwo", "joox"], 
                                       state="readonly", width=8)
        self.search_type.grid(row=0, column=1, padx=(5, 5))
        self.search_type.set("netease")
        
        ttk.Label(search_frame, text="关键词:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.grid(row=0, column=3, padx=(5, 5))
        self.search_entry.bind('<Return>', lambda e: self.search_music())
        
        ttk.Button(search_frame, text="搜索", command=self.search_music).grid(row=0, column=4, padx=5)
        ttk.Button(search_frame, text="清空", command=self.clear_results).grid(row=0, column=5, padx=5)
        
        # 搜索结果列表
        results_frame = ttk.LabelFrame(parent, text="搜索结果", padding="10")
        results_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建树状视图
        columns = ('name', 'artist', 'album', 'source')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=12)
        
        # 定义列
        self.results_tree.heading('name', text='歌曲名')
        self.results_tree.heading('artist', text='艺术家')
        self.results_tree.heading('album', text='专辑')
        self.results_tree.heading('source', text='来源')
        
        # 设置列宽
        self.results_tree.column('name', width=200)
        self.results_tree.column('artist', width=120)
        self.results_tree.column('album', width=150)
        self.results_tree.column('source', width=80, anchor='center')
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 绑定双击事件
        self.results_tree.bind("<Double-1>", self.on_song_double_click)
        
        # 操作按钮
        action_frame = ttk.Frame(results_frame)
        action_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky=tk.W)
        
        ttk.Button(action_frame, text="添加到收藏", command=self.add_to_favorites).grid(row=0, column=0, padx=2)
        ttk.Button(action_frame, text="添加到播放列表", command=self.add_to_playlist).grid(row=0, column=1, padx=2)
        ttk.Button(action_frame, text="立即播放", command=self.play_selected).grid(row=0, column=2, padx=2)
        ttk.Button(action_frame, text="下载歌曲", command=self.download_selected).grid(row=0, column=3, padx=2)
        
        # 音质选择
        ttk.Label(action_frame, text="音质:").grid(row=0, column=4, sticky=tk.W, padx=(10, 0))
        self.quality_combo = ttk.Combobox(action_frame, values=["128", "192", "320", "740", "999"], 
                                         state="readonly", width=6)
        self.quality_combo.grid(row=0, column=5, padx=(5, 0))
        self.quality_combo.set("320")
        
        # 日志窗口
        log_frame = ttk.LabelFrame(parent, text="日志", padding="10")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 设置日志记录器
        self.logger.text_widget = self.log_text
        
        # 配置网格权重
        parent.rowconfigure(1, weight=1)
        parent.rowconfigure(2, weight=1)
        results_frame.rowconfigure(0, weight=1)
        results_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
    
    def _setup_right_tab_panel(self, parent):
        """设置右侧选项卡面板"""
        # 创建笔记本（选项卡）
        self.tab_control = ttk.Notebook(parent)
        self.tab_control.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建播放器选项卡
        player_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(player_tab, text="播放器")
        self.player_window = PlayerWindow(player_tab)
        
        # 创建收藏选项卡
        favorites_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(favorites_tab, text="我的收藏")
        self._setup_favorites_tab(favorites_tab)
        
        # 创建播放列表选项卡
        playlist_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(playlist_tab, text="播放列表")
        self._setup_playlist_tab(playlist_tab)
        
        # 创建下载管理选项卡
        downloads_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(downloads_tab, text="下载管理")
        self._setup_downloads_tab(downloads_tab)
        
        # 配置网格权重
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
    
    def _setup_favorites_tab(self, parent):
        """设置收藏选项卡"""
        # 搜索收藏
        search_frame = ttk.Frame(parent, padding="5")
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(search_frame, text="搜索收藏:").grid(row=0, column=0, sticky=tk.W)
        self.fav_search_entry = ttk.Entry(search_frame, width=30)
        self.fav_search_entry.grid(row=0, column=1, padx=(5, 5))
        self.fav_search_entry.bind('<Return>', lambda e: self.search_favorites())
        
        ttk.Button(search_frame, text="搜索", command=self.search_favorites).grid(row=0, column=2, padx=2)
        ttk.Button(search_frame, text="刷新", command=self.refresh_favorites).grid(row=0, column=3, padx=2)
        
        # 收藏列表（使用树状视图）
        list_frame = ttk.LabelFrame(parent, text="收藏列表", padding="10")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建树状视图
        columns = ('name', 'artist', 'album', 'source')
        self.fav_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        # 定义列
        self.fav_tree.heading('name', text='歌曲名')
        self.fav_tree.heading('artist', text='艺术家')
        self.fav_tree.heading('album', text='专辑')
        self.fav_tree.heading('source', text='来源')
        
        # 设置列宽
        self.fav_tree.column('name', width=180)
        self.fav_tree.column('artist', width=100)
        self.fav_tree.column('album', width=120)
        self.fav_tree.column('source', width=60, anchor='center')
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.fav_tree.yview)
        self.fav_tree.configure(yscrollcommand=scrollbar.set)
        
        self.fav_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 绑定双击事件
        self.fav_tree.bind("<Double-1>", self.on_favorite_double_click)
        
        # 操作按钮
        fav_action_frame = ttk.Frame(list_frame)
        fav_action_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky=tk.W)
        
        ttk.Button(fav_action_frame, text="播放", command=self.play_selected_favorite).grid(row=0, column=0, padx=2)
        ttk.Button(fav_action_frame, text="下载", command=self.download_selected_favorite).grid(row=0, column=1, padx=2)
        ttk.Button(fav_action_frame, text="移除", command=self.remove_selected_favorite).grid(row=0, column=2, padx=2)
        ttk.Button(fav_action_frame, text="批量下载", command=self.batch_download_favorites).grid(row=0, column=3, padx=2)
        ttk.Button(fav_action_frame, text="导出列表", command=self.export_favorites_list).grid(row=0, column=4, padx=2)
        
        # 收藏统计信息
        stats_frame = ttk.Frame(parent)
        stats_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.fav_stats_label = ttk.Label(stats_frame, text="收藏数量: 0")
        self.fav_stats_label.grid(row=0, column=0, sticky=tk.W)
        
        # 批量操作
        batch_frame = ttk.Frame(parent)
        batch_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(batch_frame, text="全选", command=self.select_all_favorites).grid(row=0, column=0, padx=2)
        ttk.Button(batch_frame, text="反选", command=self.invert_selection_favorites).grid(row=0, column=1, padx=2)
        ttk.Button(batch_frame, text="清空收藏", command=self.clear_all_favorites).grid(row=0, column=2, padx=2)
        
        # 配置网格权重
        parent.rowconfigure(1, weight=1)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
    
    def _setup_playlist_tab(self, parent):
        """设置播放列表选项卡"""
        # 播放列表标题
        title_frame = ttk.Frame(parent, padding="10")
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(title_frame, text="当前播放列表", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W)
        
        # 播放列表
        list_frame = ttk.Frame(parent, padding="10")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.playlist_listbox = tk.Listbox(list_frame, height=15, width=50)
        self.playlist_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.playlist_listbox.yview)
        self.playlist_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 播放列表操作
        action_frame = ttk.Frame(parent, padding="10")
        action_frame.grid(row=2, column=0, sticky=tk.W)
        
        ttk.Button(action_frame, text="播放选中", command=self.play_selected_playlist).grid(row=0, column=0, padx=2)
        ttk.Button(action_frame, text="移除选中", command=self.remove_selected_playlist).grid(row=0, column=1, padx=2)
        ttk.Button(action_frame, text="清空列表", command=self.clear_playlist).grid(row=0, column=2, padx=2)
        ttk.Button(action_frame, text="保存列表", command=self.save_playlist).grid(row=0, column=3, padx=2)
        ttk.Button(action_frame, text="加载列表", command=self.load_playlist).grid(row=0, column=4, padx=2)
        
        # 配置网格权重
        parent.rowconfigure(1, weight=1)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
    
    def _setup_downloads_tab(self, parent):
        """设置下载管理选项卡"""
        # 下载历史
        history_frame = ttk.LabelFrame(parent, text="下载历史", padding="10")
        history_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建树状视图显示下载历史
        columns = ('filename', 'size', 'time', 'status')
        self.download_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=10)
        
        # 定义列
        self.download_tree.heading('filename', text='文件名')
        self.download_tree.heading('size', text='大小')
        self.download_tree.heading('time', text='时间')
        self.download_tree.heading('status', text='状态')
        
        # 设置列宽
        self.download_tree.column('filename', width=250)
        self.download_tree.column('size', width=80, anchor='center')
        self.download_tree.column('time', width=120, anchor='center')
        self.download_tree.column('status', width=80, anchor='center')
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.download_tree.yview)
        self.download_tree.configure(yscrollcommand=scrollbar.set)
        
        self.download_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 下载文件夹管理
        folder_frame = ttk.LabelFrame(parent, text="下载文件夹", padding="10")
        folder_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(folder_frame, text="下载路径:").grid(row=0, column=0, sticky=tk.W)
        
        self.download_path_var = tk.StringVar()
        self.download_path_var.set("downloads/")
        
        path_entry = ttk.Entry(folder_frame, textvariable=self.download_path_var, width=40)
        path_entry.grid(row=0, column=1, padx=(5, 5))
        
        ttk.Button(folder_frame, text="浏览", command=self.browse_download_folder).grid(row=0, column=2, padx=2)
        ttk.Button(folder_frame, text="打开文件夹", command=self.open_download_folder).grid(row=0, column=3, padx=2)
        
        # 操作按钮
        action_frame = ttk.Frame(parent, padding="10")
        action_frame.grid(row=2, column=0, sticky=tk.W)
        
        ttk.Button(action_frame, text="刷新列表", command=self.refresh_downloads).grid(row=0, column=0, padx=2)
        ttk.Button(action_frame, text="播放文件", command=self.play_downloaded_file).grid(row=0, column=1, padx=2)
        ttk.Button(action_frame, text="删除文件", command=self.delete_downloaded_file).grid(row=0, column=2, padx=2)
        
        # 配置网格权重
        parent.rowconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        history_frame.columnconfigure(0, weight=1)
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        self.logger.log(message, level)
    
    # ========== 下载进度对话框相关方法 ==========
    
    def _show_download_dialog(self, song_name, filename):
        """显示下载对话框"""
        if not self.root.winfo_exists():
            return
            
        # 在主线程中创建对话框
        def create_dialog():
            # 如果已有对话框，先关闭
            if hasattr(self, 'download_dialog') and self.download_dialog:
                try:
                    self.download_dialog.destroy()
                except:
                    pass
            
            # 创建下载对话框
            self.download_dialog = tk.Toplevel(self.root)
            self.download_dialog.title("下载中...")
            self.download_dialog.geometry("400x250")
            self.download_dialog.resizable(False, False)
            
            # 使对话框模态化
            self.download_dialog.transient(self.root)
            self.download_dialog.grab_set()
            
            # 设置窗口位置（居中）
            self.download_dialog.update_idletasks()
            width = self.download_dialog.winfo_width()
            height = self.download_dialog.winfo_height()
            x = (self.download_dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (self.download_dialog.winfo_screenheight() // 2) - (height // 2)
            self.download_dialog.geometry(f'+{x}+{y}')
            
            # 歌曲信息
            info_frame = ttk.Frame(self.download_dialog, padding="10")
            info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            ttk.Label(info_frame, text="歌曲:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
            song_label = ttk.Label(info_frame, text=song_name[:40] + "..." if len(song_name) > 40 else song_name, 
                                 font=("Arial", 10))
            song_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
            
            ttk.Label(info_frame, text="保存到:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
            
            # 文件名显示
            filename_text = tk.Text(info_frame, height=2, width=40, wrap=tk.WORD)
            filename_text.insert(1.0, filename)
            filename_text.config(state=tk.DISABLED)
            filename_text.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=(5, 0))
            
            # 进度条
            progress_frame = ttk.Frame(self.download_dialog, padding="10")
            progress_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            self.download_progress_var = tk.DoubleVar()
            self.download_progress_bar = ttk.Progressbar(
                progress_frame, 
                variable=self.download_progress_var,
                maximum=100,
                length=350,
                mode='determinate'
            )
            self.download_progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))
            
            # 进度标签
            self.download_status_label = ttk.Label(progress_frame, text="0% (0B / 0B)")
            self.download_status_label.grid(row=1, column=0, pady=(5, 0))
            
            # 速度标签
            self.download_speed_label = ttk.Label(progress_frame, text="速度: 计算中...")
            self.download_speed_label.grid(row=2, column=0, pady=(5, 0))
            
            # 取消按钮
            button_frame = ttk.Frame(self.download_dialog, padding="10")
            button_frame.grid(row=2, column=0, sticky=tk.E)
            
            self.download_cancel_button = ttk.Button(button_frame, text="取消下载", 
                                                    command=self._cancel_download)
            self.download_cancel_button.grid(row=0, column=0)
            
            # 初始化下载变量
            self.download_start_time = None
            self.last_downloaded = 0
            self.last_time = None
            self.is_download_cancelled = False
            self.download_progress_data = {'last_update': 0, 'progress': 0}
            
            # 配置网格权重
            info_frame.columnconfigure(1, weight=1)
            progress_frame.columnconfigure(0, weight=1)
        
        self.root.after(0, create_dialog)
    
    def _update_download_progress(self, song_name, progress, total_size, downloaded):
        """更新下载进度（安全版本）"""
        if not hasattr(self, 'download_dialog') or not self.download_dialog:
            return
        
        # 使用时间戳限制更新频率（避免递归）
        current_time = time.time()
        if current_time - self.download_progress_data['last_update'] < 0.05:  # 每秒最多20次更新
            return
            
        self.download_progress_data['last_update'] = current_time
        
        def update_ui():
            if not hasattr(self, 'download_dialog') or not self.download_dialog:
                return
                
            try:
                # 更新进度条
                if hasattr(self, 'download_progress_var'):
                    self.download_progress_var.set(progress)
                
                # 格式化文件大小
                def format_size(size):
                    if size < 1024:
                        return f"{size}B"
                    elif size < 1024 * 1024:
                        return f"{size/1024:.1f}KB"
                    elif size < 1024 * 1024 * 1024:
                        return f"{size/(1024*1024):.1f}MB"
                    else:
                        return f"{size/(1024*1024*1024):.1f}GB"
                
                # 更新状态标签
                if hasattr(self, 'download_status_label'):
                    total_str = format_size(total_size)
                    downloaded_str = format_size(downloaded)
                    self.download_status_label.config(text=f"{progress:.1f}% ({downloaded_str} / {total_str})")
                
                # 计算下载速度
                if hasattr(self, 'download_speed_label'):
                    current_time_ui = time.time()
                    if self.download_start_time is None:
                        self.download_start_time = current_time_ui
                        self.last_downloaded = downloaded
                        self.last_time = current_time_ui
                    
                    time_diff = current_time_ui - self.last_time
                    if time_diff >= 0.5:  # 每0.5秒更新一次速度
                        downloaded_diff = downloaded - self.last_downloaded
                        if downloaded_diff > 0:
                            speed = downloaded_diff / time_diff
                            
                            if speed < 1024:
                                speed_str = f"{speed:.1f} B/s"
                            elif speed < 1024 * 1024:
                                speed_str = f"{speed/1024:.1f} KB/s"
                            else:
                                speed_str = f"{speed/(1024*1024):.1f} MB/s"
                            
                            self.download_speed_label.config(text=f"速度: {speed_str}")
                            
                            # 更新上次记录
                            self.last_downloaded = downloaded
                            self.last_time = current_time_ui
                
                # 如果下载完成，更新按钮文本
                if progress >= 99.9 and hasattr(self, 'download_cancel_button'):
                    self.download_cancel_button.config(text="关闭")
                    
            except Exception as e:
                # 忽略UI更新中的错误
                pass
        
        # 在主线程中更新UI
        if self.root.winfo_exists():
            self.root.after(0, update_ui)
    
    def _cancel_download(self):
        """取消下载"""
        self.is_download_cancelled = True
        self.log("下载已取消")
        self._close_download_dialog()
    
    def _close_download_dialog(self):
        """关闭下载对话框"""
        if hasattr(self, 'download_dialog') and self.download_dialog:
            try:
                self.download_dialog.grab_release()
                self.download_dialog.destroy()
                self.download_dialog = None
            except:
                pass
    
    # ========== 下载功能相关方法 ==========
    
    def download_selected(self):
        """下载选中歌曲"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一首歌曲")
            return
        
        for item in selection:
            if item in self.song_data_cache:
                song_data = self.song_data_cache[item]
                song_id = song_data.get('id', '')
                source = self.search_type.get() if hasattr(self, 'search_type') else "netease"
                quality = self.quality_combo.get() if hasattr(self, 'quality_combo') else "320"
                
                threading.Thread(target=self._download_song_thread,
                               args=(song_id, song_data, source, quality),
                               daemon=True).start()
            else:
                self.log(f"未找到歌曲数据")
    
    def _download_song_thread(self, song_id: str, song_data: dict, source: str, quality: str):
        """下载歌曲线程"""
        try:
            song_name = song_data.get('name', '未知歌曲')
            
            # 在主线程中显示下载对话框
            def show_dialog():
                self._show_download_dialog(song_name, "")
            
            if self.root.winfo_exists():
                self.root.after(0, show_dialog)
            
            self.log(f"开始下载: {song_name}")
            
            # 获取播放链接
            url_data = self.api.get_play_url(song_id, source, quality)
            
            if url_data and isinstance(url_data, dict):
                play_url = url_data.get('url', '')
                
                if play_url:
                    # 生成文件名
                    name = song_data.get('name', '未知歌曲')
                    artist_data = song_data.get('artist', [])
                    if isinstance(artist_data, list):
                        artist_names = []
                        for artist in artist_data:
                            if isinstance(artist, dict):
                                artist_names.append(artist.get('name', ''))
                            elif isinstance(artist, str):
                                artist_names.append(artist)
                        artist_name = ' / '.join([a for a in artist_names if a])
                    else:
                        artist_name = str(artist_data)
                    
                    safe_name = self.file_handler.get_safe_filename(name)
                    safe_artist = self.file_handler.get_safe_filename(artist_name)
                    
                    # 确定文件扩展名
                    if play_url.endswith('.mp3'):
                        ext = '.mp3'
                    elif play_url.endswith('.flac'):
                        ext = '.flac'
                    elif play_url.endswith('.m4a'):
                        ext = '.m4a'
                    else:
                        ext = '.mp3'
                    
                    filename = f"downloads/{safe_name} - {safe_artist} [{quality}kbps]{ext}"
                    
                    # 更新对话框中的文件名
                    def update_filename():
                        if hasattr(self, 'download_dialog') and self.download_dialog:
                            # 更新对话框标题显示文件名
                            self.download_dialog.title(f"下载中: {name[:20]}...")
                    
                    if self.root.winfo_exists():
                        self.root.after(0, update_filename)
                    
                    # 下载文件
                    def progress_callback(progress, total_size, downloaded):
                        """进度回调函数 - 避免递归调用"""
                        # 使用时间间隔限制更新频率
                        current_time = time.time()
                        if current_time - self.download_progress_data.get('last_callback', 0) > 0.05:
                            self.download_progress_data['last_callback'] = current_time
                            
                            # 安全地更新UI
                            self._update_download_progress(song_name, progress, total_size, downloaded)
                    
                    success = self.file_handler.download_file(play_url, filename, progress_callback)
                    
                    # 关闭下载对话框
                    def close_dialog():
                        self._close_download_dialog()
                    
                    if self.root.winfo_exists():
                        self.root.after(0, close_dialog)
                    
                    if success:
                        self.log(f"下载完成: {filename}")
                        
                        def show_success():
                            messagebox.showinfo("成功", f"下载完成: {filename}")
                            # 刷新下载列表
                            if hasattr(self, 'refresh_downloads'):
                                self.refresh_downloads()
                        
                        if self.root.winfo_exists():
                            self.root.after(0, show_success)
                    else:
                        self.log(f"下载失败")
                        
                        def show_failed():
                            messagebox.showerror("错误", "下载失败")
                        
                        if self.root.winfo_exists():
                            self.root.after(0, show_failed)
                else:
                    def show_no_url():
                        messagebox.showerror("错误", "未获取到播放链接")
                    
                    if self.root.winfo_exists():
                        self.root.after(0, show_no_url)
            else:
                def show_failed():
                    messagebox.showerror("错误", "获取播放链接失败")
                
                if self.root.winfo_exists():
                    self.root.after(0, show_failed)
                    
        except Exception as e:
            error_msg = str(e)
            self.log(f"下载失败: {error_msg}", "ERROR")
            
            # 关闭下载对话框
            def close_on_error():
                self._close_download_dialog()
            
            if self.root.winfo_exists():
                self.root.after(0, close_on_error)
            
            def show_error():
                messagebox.showerror("错误", f"下载失败: {error_msg}")
            
            if self.root.winfo_exists():
                self.root.after(0, show_error)
    
    def download_selected_favorite(self):
        """下载选中的收藏歌曲"""
        if not hasattr(self, 'fav_tree') or self.fav_tree is None:
            return
            
        selection = self.fav_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一首收藏歌曲")
            return
        
        for item in selection:
            tags = self.fav_tree.item(item, 'tags')
            
            if tags:
                try:
                    song_data = json.loads(tags[0])
                    song_id = song_data.get('id', '')
                    source = song_data.get('source', 'netease')
                    quality = self.quality_combo.get() if hasattr(self, 'quality_combo') else "320"
                    
                    threading.Thread(target=self._download_song_thread,
                                   args=(song_id, song_data, source, quality),
                                   daemon=True).start()
                    
                except json.JSONDecodeError as e:
                    self.log(f"解析歌曲数据失败: {str(e)}", "ERROR")
    
    # ========== 收藏管理相关方法 ==========
    
    def refresh_favorites_display(self):
        """刷新收藏显示"""
        # 检查组件是否已初始化
        if not hasattr(self, 'fav_tree') or self.fav_tree is None:
            return
        
        # 清空当前显示
        for item in self.fav_tree.get_children():
            self.fav_tree.delete(item)
        
        # 重新加载收藏
        for song in self.favorites:
            name = song.get('name', '未知歌曲')
            
            # 处理艺术家信息
            artist_data = song.get('artist', [])
            if isinstance(artist_data, list):
                artist_names = []
                for artist in artist_data:
                    if isinstance(artist, dict):
                        artist_names.append(artist.get('name', ''))
                    elif isinstance(artist, str):
                        artist_names.append(artist)
                artist_name = ' / '.join([a for a in artist_names if a])
            else:
                artist_name = str(artist_data)
            
            album = song.get('album', '未知专辑')
            source = song.get('source', 'netease')
            
            # 来源显示
            source_map = {'netease': '网易', 'kuwo': '酷我', 'joox': 'JOOX'}
            source_str = source_map.get(source, source)
            
            # 添加到树状视图
            item_id = self.fav_tree.insert('', 'end', values=(name, artist_name, album, source_str))
            # 存储歌曲数据到item的tags中
            self.fav_tree.item(item_id, tags=(json.dumps(song, ensure_ascii=False),))
        
        # 更新统计信息
        if hasattr(self, 'fav_stats_label') and self.fav_stats_label is not None:
            self.fav_stats_label.config(text=f"收藏数量: {len(self.favorites)}")
        
        self.log(f"刷新收藏显示，共 {len(self.favorites)} 首歌曲")
    
    def search_favorites(self):
        """搜索收藏"""
        if not hasattr(self, 'fav_search_entry') or self.fav_search_entry is None:
            return
            
        keyword = self.fav_search_entry.get().strip()
        if not keyword:
            # 如果没有关键词，显示所有收藏
            self.refresh_favorites_display()
            return
        
        # 检查组件是否已初始化
        if not hasattr(self, 'fav_tree') or self.fav_tree is None:
            return
        
        # 清空当前显示
        for item in self.fav_tree.get_children():
            self.fav_tree.delete(item)
        
        matched_count = 0
        
        # 搜索收藏
        for song in self.favorites:
            name = song.get('name', '')
            artist_data = song.get('artist', [])
            
            # 构建搜索文本
            search_text = name.lower()
            
            # 添加艺术家信息到搜索文本
            if isinstance(artist_data, list):
                for artist in artist_data:
                    if isinstance(artist, dict):
                        search_text += ' ' + artist.get('name', '').lower()
                    elif isinstance(artist, str):
                        search_text += ' ' + artist.lower()
            elif isinstance(artist_data, str):
                search_text += ' ' + artist_data.lower()
            
            # 添加专辑信息
            album = song.get('album', '')
            search_text += ' ' + album.lower()
            
            # 检查是否匹配
            if keyword.lower() in search_text:
                # 显示匹配的歌曲
                artist_name = ''
                if isinstance(artist_data, list):
                    artist_names = []
                    for artist in artist_data:
                        if isinstance(artist, dict):
                            artist_names.append(artist.get('name', ''))
                        elif isinstance(artist, str):
                            artist_names.append(artist)
                    artist_name = ' / '.join([a for a in artist_names if a])
                else:
                    artist_name = str(artist_data)
                
                album = song.get('album', '未知专辑')
                source = song.get('source', 'netease')
                
                # 来源显示
                source_map = {'netease': '网易', 'kuwo': '酷我', 'joox': 'JOOX'}
                source_str = source_map.get(source, source)
                
                # 添加到树状视图
                item_id = self.fav_tree.insert('', 'end', values=(name, artist_name, album, source_str))
                # 存储歌曲数据到item的tags中
                self.fav_tree.item(item_id, tags=(json.dumps(song, ensure_ascii=False),))
                
                matched_count += 1
        
        self.log(f"在收藏中搜索 '{keyword}'，找到 {matched_count} 首歌曲")
        if hasattr(self, 'fav_stats_label') and self.fav_stats_label is not None:
            self.fav_stats_label.config(text=f"搜索到 {matched_count} 首歌曲")
    
    def refresh_favorites(self):
        """刷新收藏列表"""
        self.load_favorites()
        self.log("收藏列表已刷新")
    
    def on_favorite_double_click(self, event):
        """双击收藏播放"""
        selection = self.fav_tree.selection()
        if selection:
            self.play_selected_favorite()
    
    def play_selected_favorite(self):
        """播放选中的收藏歌曲"""
        if not hasattr(self, 'fav_tree') or self.fav_tree is None:
            messagebox.showwarning("警告", "收藏列表未初始化")
            return
            
        selection = self.fav_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一首收藏歌曲")
            return
        
        item = selection[0]
        tags = self.fav_tree.item(item, 'tags')
        
        if tags:
            try:
                song_data = json.loads(tags[0])
                song_id = song_data.get('id', '')
                source = song_data.get('source', 'netease')
                quality = self.quality_combo.get() if hasattr(self, 'quality_combo') else "320"
                
                self.log(f"播放收藏歌曲: {song_data.get('name', '未知歌曲')}")
                
                # 在新线程中获取播放链接
                threading.Thread(target=self._get_and_play_song,
                               args=(song_id, song_data, source, quality),
                               daemon=True).start()
                
                # 切换到播放器选项卡
                if hasattr(self, 'tab_control'):
                    self.tab_control.select(0)  # 0是播放器选项卡
                
            except json.JSONDecodeError as e:
                self.log(f"解析歌曲数据失败: {str(e)}", "ERROR")
    
    def remove_selected_favorite(self):
        """移除选中的收藏歌曲"""
        if not hasattr(self, 'fav_tree') or self.fav_tree is None:
            return
            
        selection = self.fav_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要移除的歌曲")
            return
        
        # 确认删除
        if not messagebox.askyesno("确认", f"确定要移除选中的 {len(selection)} 首歌曲吗？"):
            return
        
        removed_count = 0
        
        for item in selection:
            tags = self.fav_tree.item(item, 'tags')
            
            if tags:
                try:
                    song_data = json.loads(tags[0])
                    song_id = song_data.get('id', '')
                    
                    # 从收藏列表中移除
                    self.favorites = [fav for fav in self.favorites if fav.get('id') != song_id]
                    
                    removed_count += 1
                    
                except json.JSONDecodeError as e:
                    self.log(f"解析歌曲数据失败: {str(e)}", "ERROR")
        
        if removed_count > 0:
            # 保存更改
            self.save_favorites()
            
            # 刷新显示
            self.refresh_favorites_display()
            
            self.log(f"已移除 {removed_count} 首歌曲")
            messagebox.showinfo("成功", f"已移除 {removed_count} 首歌曲")
        else:
            messagebox.showwarning("警告", "没有歌曲被移除")
    
    def batch_download_favorites(self):
        """批量下载收藏歌曲"""
        if not self.favorites:
            messagebox.showwarning("警告", "收藏列表为空")
            return
        
        # 让用户选择要下载的歌曲
        download_window = tk.Toplevel(self.root)
        download_window.title("批量下载")
        download_window.geometry("500x400")
        
        # 创建选择列表
        list_frame = ttk.Frame(download_window, padding="10")
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 多选列表框
        download_select_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=15)
        download_select_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=download_select_listbox.yview)
        download_select_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 添加所有收藏歌曲到列表
        for song in self.favorites:
            name = song.get('name', '未知歌曲')
            artist_data = song.get('artist', [])
            
            if isinstance(artist_data, list):
                artist_names = []
                for artist in artist_data:
                    if isinstance(artist, dict):
                        artist_names.append(artist.get('name', ''))
                    elif isinstance(artist, str):
                        artist_names.append(artist)
                artist_name = ' / '.join([a for a in artist_names if a])
            else:
                artist_name = str(artist_data)
            
            display_text = f"{name} - {artist_name}"
            download_select_listbox.insert(tk.END, display_text)
        
        # 操作按钮
        button_frame = ttk.Frame(download_window, padding="10")
        button_frame.grid(row=1, column=0, sticky=tk.W)
        
        ttk.Button(button_frame, text="全选", command=lambda: download_select_listbox.select_set(0, tk.END)).grid(row=0, column=0, padx=2)
        ttk.Button(button_frame, text="全不选", command=lambda: download_select_listbox.selection_clear(0, tk.END)).grid(row=0, column=1, padx=2)
        
        # 音质选择
        ttk.Label(button_frame, text="音质:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        batch_quality_combo = ttk.Combobox(button_frame, values=["128", "192", "320", "740", "999"], 
                                          state="readonly", width=6)
        batch_quality_combo.grid(row=0, column=3, padx=(5, 0))
        batch_quality_combo.set("320")
        
        def start_batch_download():
            """开始批量下载"""
            selected_indices = download_select_listbox.curselection()
            
            if not selected_indices:
                messagebox.showwarning("警告", "请选择要下载的歌曲")
                return
            
            quality = batch_quality_combo.get()
            download_count = len(selected_indices)
            
            download_window.destroy()
            
            self.log(f"开始批量下载 {download_count} 首歌曲，音质: {quality}kbps")
            
            # 在新线程中批量下载
            threading.Thread(target=self._batch_download_thread,
                            args=(selected_indices, quality),
                            daemon=True).start()
        
        ttk.Button(button_frame, text="开始下载", command=start_batch_download).grid(row=0, column=4, padx=2)
        ttk.Button(button_frame, text="取消", command=download_window.destroy).grid(row=0, column=5, padx=2)
        
        # 配置网格权重
        download_window.rowconfigure(0, weight=1)
        download_window.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
    
    def _batch_download_thread(self, indices, quality):
        """批量下载线程"""
        total = len(indices)
        completed = 0
        
        for idx in indices:
            if idx < len(self.favorites):
                song_data = self.favorites[idx]
                song_id = song_data.get('id', '')
                source = song_data.get('source', 'netease')
                
                try:
                    self.log(f"批量下载 ({completed+1}/{total}): {song_data.get('name', '未知歌曲')}")
                    
                    # 获取播放链接
                    url_data = self.api.get_play_url(song_id, source, quality)
                    
                    if url_data and isinstance(url_data, dict):
                        play_url = url_data.get('url', '')
                        
                        if play_url:
                            # 下载文件
                            success = self._download_single_file(play_url, song_data, quality)
                            
                            if success:
                                self.log(f"下载成功 ({completed+1}/{total})")
                            else:
                                self.log(f"下载失败 ({completed+1}/{total})")
                    
                    completed += 1
                    
                    # 更新进度
                    progress = (completed / total) * 100
                    self.root.after(0, lambda p=progress: 
                                  self.log(f"批量下载进度: {p:.1f}%"))
                    
                except Exception as e:
                    self.log(f"批量下载出错: {str(e)}", "ERROR")
        
        self.log(f"批量下载完成，共下载 {completed}/{total} 首歌曲")
        self.root.after(0, lambda: messagebox.showinfo("完成", f"批量下载完成，共下载 {completed}/{total} 首歌曲"))
    
    def _download_single_file(self, play_url, song_data, quality):
        """下载单个文件（用于批量下载）"""
        try:
            # 生成文件名
            name = song_data.get('name', '未知歌曲')
            artist_data = song_data.get('artist', [])
            if isinstance(artist_data, list):
                artist_names = []
                for artist in artist_data:
                    if isinstance(artist, dict):
                        artist_names.append(artist.get('name', ''))
                    elif isinstance(artist, str):
                        artist_names.append(artist)
                artist_name = ' / '.join([a for a in artist_names if a])
            else:
                artist_name = str(artist_data)
            
            safe_name = self.file_handler.get_safe_filename(name)
            safe_artist = self.file_handler.get_safe_filename(artist_name)
            
            # 确定文件扩展名
            if play_url.endswith('.mp3'):
                ext = '.mp3'
            elif play_url.endswith('.flac'):
                ext = '.flac'
            elif play_url.endswith('.m4a'):
                ext = '.m4a'
            else:
                ext = '.mp3'
            
            filename = f"downloads/{safe_name} - {safe_artist} [{quality}kbps]{ext}"
            
            # 下载文件（批量下载时不显示进度对话框）
            return self.file_handler.download_file(play_url, filename)
                
        except Exception as e:
            self.log(f"下载文件出错: {str(e)}", "ERROR")
            return False
    
    def export_favorites_list(self):
        """导出收藏列表"""
        if not self.favorites:
            messagebox.showwarning("警告", "收藏列表为空")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"favorites_export_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=== 我的音乐收藏列表 ===\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"歌曲数量: {len(self.favorites)}\n")
                f.write("=" * 40 + "\n\n")
                
                for i, song in enumerate(self.favorites, 1):
                    name = song.get('name', '未知歌曲')
                    
                    # 处理艺术家信息
                    artist_data = song.get('artist', [])
                    if isinstance(artist_data, list):
                        artist_names = []
                        for artist in artist_data:
                            if isinstance(artist, dict):
                                artist_names.append(artist.get('name', ''))
                            elif isinstance(artist, str):
                                artist_names.append(artist)
                        artist_name = ' / '.join([a for a in artist_names if a])
                    else:
                        artist_name = str(artist_data)
                    
                    album = song.get('album', '未知专辑')
                    source = song.get('source', 'netease')
                    
                    f.write(f"{i:3d}. {name}\n")
                    f.write(f"     艺术家: {artist_name}\n")
                    f.write(f"     专辑: {album}\n")
                    f.write(f"     来源: {source}\n")
                    f.write(f"     歌曲ID: {song.get('id', '未知')}\n\n")
            
            messagebox.showinfo("成功", f"收藏列表已导出到: {filename}")
            self.log(f"收藏列表导出到: {filename}")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def select_all_favorites(self):
        """全选收藏"""
        if hasattr(self, 'fav_tree') and self.fav_tree is not None:
            self.fav_tree.selection_set(self.fav_tree.get_children())
    
    def invert_selection_favorites(self):
        """反选收藏"""
        if not hasattr(self, 'fav_tree') or self.fav_tree is None:
            return
            
        all_items = set(self.fav_tree.get_children())
        selected_items = set(self.fav_tree.selection())
        
        # 计算反选后的选择
        new_selection = all_items - selected_items
        self.fav_tree.selection_set(tuple(new_selection))
    
    def clear_all_favorites(self):
        """清空所有收藏"""
        if not self.favorites:
            messagebox.showwarning("警告", "收藏列表已为空")
            return
        
        if messagebox.askyesno("确认", f"确定要清空所有收藏吗？共 {len(self.favorites)} 首歌曲"):
            self.favorites.clear()
            self.save_favorites()
            self.refresh_favorites_display()
            self.log("已清空所有收藏")
            messagebox.showinfo("成功", "已清空所有收藏")
    
    # ========== 播放列表相关方法 ==========
    
    def add_to_playlist(self):
        """添加到播放列表"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一首歌曲")
            return
        
        item = selection[0]
        
        if item in self.song_data_cache:
            song_data = self.song_data_cache[item]
            self.current_playlist.append(song_data)
            
            # 更新播放列表显示
            name = song_data.get('name', '未知歌曲')
            artist_data = song_data.get('artist', [])
            if isinstance(artist_data, list):
                artist_names = []
                for artist in artist_data:
                    if isinstance(artist, dict):
                        artist_names.append(artist.get('name', ''))
                    elif isinstance(artist, str):
                        artist_names.append(artist)
                artist_name = ' / '.join([a for a in artist_names if a])
            else:
                artist_name = str(artist_data)
            
            display_text = f"{name} - {artist_name}"
            self.playlist_listbox.insert(tk.END, display_text)
            
            self.log(f"已添加到播放列表: {name}")
        else:
            self.log(f"未找到歌曲数据")
    
    def play_selected_playlist(self):
        """播放选中的播放列表歌曲"""
        selection = self.playlist_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一首歌曲")
            return
        
        index = selection[0]
        if 0 <= index < len(self.current_playlist):
            song_data = self.current_playlist[index]
            song_id = song_data.get('id', '')
            source = song_data.get('source', 'netease')
            quality = self.quality_combo.get() if hasattr(self, 'quality_combo') else "320"
            
            self.log(f"播放播放列表歌曲: {song_data.get('name', '未知歌曲')}")
            
            threading.Thread(target=self._get_and_play_song,
                           args=(song_id, song_data, source, quality),
                           daemon=True).start()
            
            # 切换到播放器选项卡
            if hasattr(self, 'tab_control'):
                self.tab_control.select(0)
    
    def remove_selected_playlist(self):
        """移除选中的播放列表歌曲"""
        selection = self.playlist_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要移除的歌曲")
            return
        
        # 从后往前移除，避免索引变化
        for idx in sorted(selection, reverse=True):
            if 0 <= idx < len(self.current_playlist):
                song_name = self.current_playlist[idx].get('name', '未知歌曲')
                del self.current_playlist[idx]
                self.playlist_listbox.delete(idx)
                self.log(f"已从播放列表移除: {song_name}")
    
    def clear_playlist(self):
        """清空播放列表"""
        if not self.current_playlist:
            messagebox.showwarning("警告", "播放列表已为空")
            return
        
        if messagebox.askyesno("确认", f"确定要清空播放列表吗？共 {len(self.current_playlist)} 首歌曲"):
            self.current_playlist.clear()
            self.playlist_listbox.delete(0, tk.END)
            self.log("已清空播放列表")
    
    def save_playlist(self):
        """保存播放列表"""
        if not self.current_playlist:
            messagebox.showwarning("警告", "播放列表为空")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"playlist_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.current_playlist, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", f"播放列表已保存到: {filename}")
            self.log(f"播放列表保存到: {filename}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def load_playlist(self):
        """加载播放列表"""
        try:
            filename = filedialog.askopenfilename(
                title="选择播放列表文件",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.current_playlist = json.load(f)
                
                # 更新播放列表显示
                self.playlist_listbox.delete(0, tk.END)
                for song in self.current_playlist:
                    name = song.get('name', '未知歌曲')
                    artist_data = song.get('artist', [])
                    if isinstance(artist_data, list):
                        artist_names = []
                        for artist in artist_data:
                            if isinstance(artist, dict):
                                artist_names.append(artist.get('name', ''))
                            elif isinstance(artist, str):
                                artist_names.append(artist)
                        artist_name = ' / '.join([a for a in artist_names if a])
                    else:
                        artist_name = str(artist_data)
                    
                    display_text = f"{name} - {artist_name}"
                    self.playlist_listbox.insert(tk.END, display_text)
                
                self.log(f"播放列表已加载: {filename}")
                messagebox.showinfo("成功", f"播放列表已加载，共 {len(self.current_playlist)} 首歌曲")
                
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {str(e)}")
    
    # ========== 下载管理相关方法 ==========
    
    def browse_download_folder(self):
        """浏览下载文件夹"""
        folder = filedialog.askdirectory(title="选择下载文件夹")
        if folder:
            self.download_path_var.set(folder + "/")
    
    def open_download_folder(self):
        """打开下载文件夹"""
        import subprocess
        
        folder = self.download_path_var.get()
        if os.path.exists(folder):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(folder)
                elif os.name == 'posix':  # Linux/Mac
                    subprocess.run(['xdg-open', folder])
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件夹: {str(e)}")
        else:
            messagebox.showwarning("警告", "文件夹不存在")
    
    def refresh_downloads(self):
        """刷新下载列表"""
        # 清空当前显示
        for item in self.download_tree.get_children():
            self.download_tree.delete(item)
        
        folder = self.download_path_var.get()
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        
        # 遍历下载文件夹
        file_count = 0
        total_size = 0
        
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath):
                # 获取文件信息
                size = os.path.getsize(filepath)
                mtime = os.path.getmtime(filepath)
                mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                
                # 转换文件大小
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.1f}KB"
                else:
                    size_str = f"{size/(1024*1024):.1f}MB"
                
                # 添加到树状视图
                self.download_tree.insert('', 'end', values=(filename, size_str, mtime_str, "已完成"))
                
                file_count += 1
                total_size += size
        
        self.log(f"下载文件夹: {folder}, 文件数: {file_count}, 总大小: {total_size/(1024*1024):.1f}MB")
    
    def play_downloaded_file(self):
        """播放下载的文件"""
        selection = self.download_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文件")
            return
        
        item = selection[0]
        filename = self.download_tree.item(item, 'values')[0]
        folder = self.download_path_var.get()
        filepath = os.path.join(folder, filename)
        
        if os.path.exists(filepath):
            # 创建临时的歌曲数据
            song_data = {
                'name': os.path.splitext(filename)[0],
                'artist': '本地文件',
                'album': '下载文件夹',
                'source': 'local'
            }
            
            # 播放本地文件
            self.player_window.play_song(song_data, filepath)
            
            # 切换到播放器选项卡
            if hasattr(self, 'tab_control'):
                self.tab_control.select(0)
            
            self.log(f"播放本地文件: {filename}")
        else:
            messagebox.showerror("错误", "文件不存在")
    
    def delete_downloaded_file(self):
        """删除下载的文件"""
        selection = self.download_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文件")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的文件吗？"):
            for item in selection:
                filename = self.download_tree.item(item, 'values')[0]
                folder = self.download_path_var.get()
                filepath = os.path.join(folder, filename)
                
                try:
                    os.remove(filepath)
                    self.download_tree.delete(item)
                    self.log(f"已删除文件: {filename}")
                except Exception as e:
                    messagebox.showerror("错误", f"删除失败: {str(e)}")
            
            self.log("文件删除完成")
    
    # ========== 原有的其他方法 ==========
    
    def load_favorites(self):
        """加载收藏列表"""
        try:
            self.favorites = self.file_handler.load_favorites()
            self.log(f"加载收藏列表，共 {len(self.favorites)} 首歌曲")
            
            # UI初始化后刷新显示
            if hasattr(self, 'fav_tree') and self.fav_tree is not None:
                self.refresh_favorites_display()
        except Exception as e:
            self.log(f"加载收藏失败: {str(e)}", "ERROR")
            self.favorites = []
    
    def search_music(self):
        """搜索音乐"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return
        
        source = self.search_type.get()
        
        # 清空当前结果和缓存
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.song_data_cache.clear()
        
        self.log(f"开始搜索: {keyword}")
        
        # 在新线程中执行搜索
        threading.Thread(target=self._search_music_thread, 
                        args=(keyword, source), 
                        daemon=True).start()
    
    def _search_music_thread(self, keyword: str, source: str):
        """搜索音乐线程"""
        try:
            results = self.api.search(keyword, source)
            
            if results:
                # 使用安全的方式更新UI
                def update_ui():
                    try:
                        self._display_search_results(results, source)
                        self.log(f"找到 {len(results)} 首歌曲")
                    except Exception as e:
                        self.log(f"显示搜索结果失败: {str(e)}", "ERROR")
                
                # 安全地调用after方法
                if self.root.winfo_exists():
                    self.root.after(0, update_ui)
                else:
                    self.log("主窗口已关闭，无法更新UI", "ERROR")
            else:
                def show_no_results():
                    messagebox.showinfo("提示", "未找到相关歌曲")
                
                if self.root.winfo_exists():
                    self.root.after(0, show_no_results)
                
        except Exception as e:
            self.log(f"搜索失败: {str(e)}", "ERROR")
            def show_error():
                messagebox.showerror("错误", f"搜索失败: {str(e)}")
            
            if self.root.winfo_exists():
                self.root.after(0, show_error)
    
    def _display_search_results(self, songs: list, source: str):
        """显示搜索结果"""
        for song in songs:
            if not isinstance(song, dict):
                continue
            
            # 提取歌曲信息
            name = song.get('name', '未知歌曲')
            
            # 处理艺术家信息
            artist_data = song.get('artist', [])
            if isinstance(artist_data, list):
                artist_names = []
                for artist in artist_data:
                    if isinstance(artist, dict):
                        artist_names.append(artist.get('name', ''))
                    elif isinstance(artist, str):
                        artist_names.append(artist)
                artist_name = ' / '.join([a for a in artist_names if a])
            else:
                artist_name = str(artist_data)
            
            album = song.get('album', '未知专辑')
            
            # 来源显示
            source_map = {'netease': '网易', 'kuwo': '酷我', 'joox': 'JOOX'}
            source_str = source_map.get(source, source)
            
            # 添加到树状视图
            item_id = self.results_tree.insert('', 'end', values=(name, artist_name, album, source_str))
            
            # 将完整数据存储到缓存
            self.song_data_cache[item_id] = song
    
    def clear_results(self):
        """清空搜索结果"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.song_data_cache.clear()
        self.search_entry.delete(0, tk.END)
        if hasattr(self, 'info_text'):
            self.info_text.delete(1.0, tk.END)
    
    def on_song_double_click(self, event):
        """双击歌曲播放"""
        selection = self.results_tree.selection()
        if selection:
            self.play_selected()
    
    def play_selected(self):
        """播放选中歌曲"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一首歌曲")
            return
        
        item = selection[0]
        
        # 从缓存获取歌曲数据
        if item in self.song_data_cache:
            song_data = self.song_data_cache[item]
            song_id = song_data.get('id', '')
            source = self.search_type.get() if hasattr(self, 'search_type') else "netease"
            quality = self.quality_combo.get() if hasattr(self, 'quality_combo') else "320"
            
            self.log(f"获取播放链接: {song_data.get('name', '未知歌曲')}")
            
            # 在新线程中获取播放链接
            threading.Thread(target=self._get_and_play_song,
                           args=(song_id, song_data, source, quality),
                           daemon=True).start()
            
            # 切换到播放器选项卡
            if hasattr(self, 'tab_control'):
                self.tab_control.select(0)
        else:
            self.log(f"未找到歌曲数据")
    
    def _get_and_play_song(self, song_id: str, song_data: dict, source: str, quality: str):
        """获取并播放歌曲"""
        try:
            # 获取播放链接
            url_data = self.api.get_play_url(song_id, source, quality)
            
            if url_data and isinstance(url_data, dict):
                play_url = url_data.get('url', '')
                
                if play_url:
                    def play_song():
                        try:
                            self.player_window.play_song(song_data, play_url)
                            self.log(f"开始播放: {song_data.get('name', '未知歌曲')}")
                            
                            # 显示歌曲信息
                            self._show_song_info(song_data, url_data)
                        except Exception as e:
                            self.log(f"播放失败: {str(e)}", "ERROR")
                            # 仅记录错误，不弹窗，因为可能已经在播放
                    
                    if self.root.winfo_exists():
                        self.root.after(0, play_song)
                else:
                    def show_no_url():
                        messagebox.showerror("错误", "未获取到播放链接")
                    
                    if self.root.winfo_exists():
                        self.root.after(0, show_no_url)
            else:
                def show_failed():
                    messagebox.showerror("错误", "获取播放链接失败")
                
                if self.root.winfo_exists():
                    self.root.after(0, show_failed)
                    
        except Exception as e:
            self.log(f"获取播放链接失败: {str(e)}", "ERROR")
            def show_error():
                messagebox.showerror("错误", f"获取播放链接失败: {str(e)}")
            
            if self.root.winfo_exists():
                self.root.after(0, show_error)
    
    def _show_song_info(self, song_data: dict, url_data: dict):
        """显示歌曲信息"""
        if not hasattr(self, 'info_text'):
            return
            
        info = f"歌曲: {song_data.get('name', '未知歌曲')}\n"
        
        # 处理艺术家信息
        artist_data = song_data.get('artist', [])
        if isinstance(artist_data, list):
            artist_names = []
            for artist in artist_data:
                if isinstance(artist, dict):
                    artist_names.append(artist.get('name', ''))
                elif isinstance(artist, str):
                    artist_names.append(artist)
            artist_name = ' / '.join([a for a in artist_names if a])
        else:
            artist_name = str(artist_data)
        
        info += f"艺术家: {artist_name}\n"
        info += f"专辑: {song_data.get('album', '未知专辑')}\n"
        
        if url_data:
            info += f"音质: {url_data.get('br', '未知')}kbps\n"
            info += f"文件大小: {url_data.get('size', '未知')}KB\n"
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
    
    def add_to_favorites(self):
        """添加到收藏"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一首歌曲")
            return
        
        added_count = 0
        already_exists_count = 0
        
        for item in selection:
            if item in self.song_data_cache:
                song_data = self.song_data_cache[item]
                
                # 避免重复添加
                song_id = song_data.get('id', '')
                if not any(fav.get('id') == song_id for fav in self.favorites):
                    self.favorites.append(song_data)
                    added_count += 1
                    
                    self.log(f"已添加到收藏: {song_data.get('name', '未知歌曲')}")
                else:
                    already_exists_count += 1
                    self.log(f"歌曲已存在于收藏中: {song_data.get('name', '未知歌曲')}")
            else:
                self.log(f"未找到歌曲数据")
        
        if added_count > 0:
            # 保存收藏
            self.save_favorites()
            
            # 立即刷新收藏显示
            self.refresh_favorites_display()
            
            # 切换到收藏选项卡
            if hasattr(self, 'tab_control'):
                self.tab_control.select(1)  # 1是收藏选项卡
            
            # 显示成功消息
            if already_exists_count > 0:
                messagebox.showinfo("成功", f"已添加 {added_count} 首新歌曲到收藏\n{already_exists_count} 首歌曲已存在")
            else:
                messagebox.showinfo("成功", f"已添加 {added_count} 首歌曲到收藏")
        elif already_exists_count > 0:
            # 切换到收藏选项卡
            if hasattr(self, 'tab_control'):
                self.tab_control.select(1)
            
            # 显示提示消息
            messagebox.showinfo("提示", f"所有选中的歌曲都已存在于收藏中")
        else:
            messagebox.showinfo("提示", "没有歌曲被添加到收藏")
    
    def download_favorite(self):
        """下载收藏的歌曲"""
        self.download_selected_favorite()
    
    def remove_favorite(self):
        """移除收藏"""
        self.remove_selected_favorite()
    
    def clear_favorites(self):
        """清空收藏"""
        self.clear_all_favorites()
    
    def save_favorites(self):
        """保存收藏列表"""
        try:
            self.file_handler.save_favorites(self.favorites)
            self.log("收藏列表已保存")
        except Exception as e:
            self.log(f"保存收藏失败: {str(e)}", "ERROR")