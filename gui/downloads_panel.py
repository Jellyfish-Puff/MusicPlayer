# gui/downloads_panel.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
from datetime import datetime
from .base_panel import BasePanel

class DownloadsPanel(BasePanel):
    """下载管理面板"""

    def __init__(self, parent, main_app):
        # 先设置属性，然后调用父类初始化
        self.download_path = "downloads/"  # 先设置这个属性
        self.download_history = []
        self.download_queue_items = {}  # 添加下载队列相关变量
        super().__init__(parent, main_app)  # 然后调用父类初始化

    def setup_ui(self):
        """设置下载管理界面"""
        # 下载文件夹设置
        folder_frame = ttk.LabelFrame(self.frame, text="下载文件夹设置", padding="10")
        folder_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(folder_frame, text="下载路径:").grid(row=0, column=0, sticky=tk.W)

        self.download_path_var = tk.StringVar()
        self.download_path_var.set(self.download_path)

        self.path_entry = ttk.Entry(folder_frame, textvariable=self.download_path_var, width=40)
        self.path_entry.grid(row=0, column=1, padx=(5, 5), sticky=(tk.W, tk.E))

        ttk.Button(folder_frame, text="浏览", command=self.browse_download_folder).grid(row=0, column=2, padx=2)
        ttk.Button(folder_frame, text="打开文件夹", command=self.open_download_folder).grid(row=0, column=3, padx=2)
        ttk.Button(folder_frame, text="应用", command=self.apply_download_path).grid(row=0, column=4, padx=2)

        # 下载队列管理
        queue_frame = ttk.LabelFrame(self.frame, text="下载队列", padding="10")
        queue_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # 创建下载队列树状视图
        queue_columns = ('name', 'artist', 'progress', 'status', 'speed')
        self.queue_tree = ttk.Treeview(queue_frame, columns=queue_columns, show='headings', height=4)

        # 定义列
        self.queue_tree.heading('name', text='歌曲名')
        self.queue_tree.heading('artist', text='艺术家')
        self.queue_tree.heading('progress', text='进度')
        self.queue_tree.heading('status', text='状态')
        self.queue_tree.heading('speed', text='速度')

        # 设置列宽
        self.queue_tree.column('name', width=180)
        self.queue_tree.column('artist', width=120)
        self.queue_tree.column('progress', width=80, anchor='center')
        self.queue_tree.column('status', width=100, anchor='center')
        self.queue_tree.column('speed', width=80, anchor='center')

        # 添加滚动条
        queue_scrollbar = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=queue_scrollbar.set)

        self.queue_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        queue_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 下载队列操作按钮
        queue_action_frame = ttk.Frame(queue_frame)
        queue_action_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky=tk.W)

        ttk.Button(queue_action_frame, text="刷新队列", command=self.update_download_queue).grid(row=0, column=0, padx=2)
        ttk.Button(queue_action_frame, text="取消选中", command=self.cancel_selected_download).grid(row=0, column=1, padx=2)
        ttk.Button(queue_action_frame, text="全部取消", command=self.cancel_all_downloads).grid(row=0, column=2, padx=2)

        # 下载历史列表
        history_frame = ttk.LabelFrame(self.frame, text="下载历史/本地文件", padding="10")
        history_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # 创建树状视图显示下载历史和本地文件
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

        # 下载操作按钮
        action_frame = ttk.Frame(history_frame)
        action_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky=tk.W)

        ttk.Button(action_frame, text="刷新列表", command=self.refresh_downloads).grid(row=0, column=0, padx=2)
        ttk.Button(action_frame, text="播放文件", command=self.play_downloaded_file).grid(row=0, column=1, padx=2)
        ttk.Button(action_frame, text="删除文件", command=self.delete_downloaded_file).grid(row=0, column=2, padx=2)
        ttk.Button(action_frame, text="清除历史", command=self.clear_download_history).grid(row=0, column=3, padx=2)

        # 下载统计
        stats_frame = ttk.Frame(self.frame)
        stats_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))

        self.stats_label = ttk.Label(stats_frame, text="文件数: 0 | 总大小: 0MB")
        self.stats_label.grid(row=0, column=0, sticky=tk.W)

        # 配置网格权重
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)  # 历史框架占主要空间
        queue_frame.rowconfigure(0, weight=1)
        queue_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        history_frame.columnconfigure(0, weight=1)
        folder_frame.columnconfigure(1, weight=1)

        # 初始化下载文件夹
        self._init_download_folder()
        # 初始化下载队列显示
        self.update_download_queue()

    def _init_download_folder(self):
        """初始化下载文件夹"""
        # 确保下载文件夹存在
        if not os.path.exists(self.download_path):
            try:
                os.makedirs(self.download_path, exist_ok=True)
                self.log(f"创建下载目录: {self.download_path}")
            except Exception as e:
                self.log(f"创建下载目录失败: {str(e)}", "ERROR")

        # 加载下载历史
        self._load_download_history()

        # 刷新下载列表显示
        self.refresh_downloads()

    def browse_download_folder(self):
        """浏览下载文件夹"""
        folder = filedialog.askdirectory(title="选择下载文件夹", initialdir=self.download_path)
        if folder:
            self.download_path_var.set(folder + "/")

    def open_download_folder(self):
        """打开下载文件夹"""
        folder = self.download_path_var.get()
        if os.path.exists(folder):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(folder)
                elif os.name == 'posix':  # Linux/Mac
                    import subprocess
                    subprocess.run(['xdg-open', folder])
            except Exception as e:
                self.show_message("错误", f"无法打开文件夹: {str(e)}", "error")
        else:
            self.show_message("警告", "文件夹不存在", "warning")

    def apply_download_path(self):
        """应用下载路径设置"""
        new_path = self.download_path_var.get()
        if not new_path.endswith('/') and not new_path.endswith('\\'):
            new_path += '/'

        # 检查路径是否存在
        if not os.path.exists(new_path):
            try:
                os.makedirs(new_path, exist_ok=True)
                self.log(f"创建下载目录: {new_path}")
            except Exception as e:
                self.show_message("错误", f"无法创建目录: {str(e)}", "error")
                return

        self.download_path = new_path
        self.log(f"下载路径已设置为: {new_path}")
        self.refresh_downloads()

    def update_download_queue(self):
        """更新下载队列显示"""
        # 清空当前显示
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)

        # 清空队列项目映射
        self.download_queue_items.clear()

        # 获取下载队列
        if hasattr(self.main_app, 'get_download_queue'):
            queue = self.main_app.get_download_queue()

            for download_item in queue:
                name = download_item.get('name', '未知歌曲')
                artist = self._format_artist(download_item.get('artist', ''))
                progress = download_item.get('progress', 0)
                status = download_item.get('status', '未知')
                speed = download_item.get('speed', '')

                # 进度显示
                progress_str = f"{progress:.1f}%" if progress > 0 else "等待中"

                # 添加到树状视图
                item_id = self.queue_tree.insert('', 'end', values=(name, artist, progress_str, status, speed))

                # 保存下载项ID
                self.download_queue_items[item_id] = download_item.get('id', '')

        self.log(f"更新下载队列，共 {len(self.download_queue_items)} 个任务")

    def update_download_progress(self, download_item):
        """更新单个下载项的进度"""
        # 查找对应的项目
        for item_id, download_id in self.download_queue_items.items():
            if download_id == download_item.get('id', ''):
                name = download_item.get('name', '未知歌曲')
                artist = self._format_artist(download_item.get('artist', ''))
                progress = download_item.get('progress', 0)
                status = download_item.get('status', '未知')
                speed = download_item.get('speed', '')

                # 进度显示
                progress_str = f"{progress:.1f}%" if progress > 0 else "等待中"

                # 更新树状视图项目
                self.queue_tree.item(item_id, values=(name, artist, progress_str, status, speed))
                break

    def cancel_selected_download(self):
        """取消选中的下载"""
        selection = self.queue_tree.selection()
        if not selection:
            self.show_message("警告", "请先选择一个下载任务", "warning")
            return

        cancelled_count = 0
        for item_id in selection:
            download_id = self.download_queue_items.get(item_id)
            if download_id and hasattr(self.main_app, 'cancel_download'):
                if self.main_app.cancel_download(download_id):
                    self.queue_tree.delete(item_id)
                    del self.download_queue_items[item_id]
                    cancelled_count += 1

        if cancelled_count > 0:
            self.log(f"已取消 {cancelled_count} 个下载任务")
            self.show_message("成功", f"已取消 {cancelled_count} 个下载任务", "info")

    def cancel_all_downloads(self):
        """取消所有下载"""
        if not self.show_message("确认", "确定要取消所有下载任务吗？", "ask"):
            return

        if hasattr(self.main_app, 'cancel_all_downloads'):
            self.main_app.cancel_all_downloads()

            # 清空队列显示
            for item in self.queue_tree.get_children():
                self.queue_tree.delete(item)
            self.download_queue_items.clear()

            self.log("已取消所有下载任务")
            self.show_message("成功", "已取消所有下载任务", "info")

    def refresh_downloads(self):
        """刷新下载列表"""
        # 清空当前显示
        for item in self.download_tree.get_children():
            self.download_tree.delete(item)

        folder = self.download_path
        if not os.path.exists(folder):
            try:
                os.makedirs(folder, exist_ok=True)
                self.log(f"创建目录: {folder}")
            except Exception as e:
                self.show_message("错误", f"无法创建目录: {str(e)}", "error")
                return

        # 遍历下载文件夹
        file_count = 0
        total_size = 0

        try:
            for filename in os.listdir(folder):
                filepath = os.path.join(folder, filename)
                if os.path.isfile(filepath):
                    # 获取文件信息
                    size = os.path.getsize(filepath)
                    mtime = os.path.getmtime(filepath)
                    mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')

                    # 转换文件大小
                    size_str = self._format_file_size(size)

                    # 检查文件扩展名，确定是否为音频文件
                    file_ext = os.path.splitext(filename)[1].lower()
                    is_audio = file_ext in ['.mp3', '.flac', '.m4a', '.wav', '.aac', '.ogg']

                    status = "音频文件" if is_audio else "其他文件"

                    # 添加到树状视图
                    self.download_tree.insert('', 'end', values=(filename, size_str, mtime_str, status))

                    file_count += 1
                    total_size += size

            # 更新统计信息
            total_size_mb = total_size / (1024 * 1024)
            self.stats_label.config(text=f"文件数: {file_count} | 总大小: {total_size_mb:.1f}MB")

            self.log(f"下载文件夹: {folder}, 文件数: {file_count}, 总大小: {total_size_mb:.1f}MB")

        except Exception as e:
            self.log(f"刷新下载列表失败: {str(e)}", "ERROR")
            self.show_message("错误", f"刷新失败: {str(e)}", "error")

    def play_downloaded_file(self):
        """播放下载的文件"""
        selection = self.download_tree.selection()
        if not selection:
            self.show_message("警告", "请先选择一个文件", "warning")
            return

        item = selection[0]
        values = self.download_tree.item(item, 'values')
        if not values:
            return

        filename = values[0]
        folder = self.download_path
        filepath = os.path.join(folder, filename)

        if os.path.exists(filepath):
            # 检查文件是否为音频文件
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in ['.mp3', '.flac', '.m4a', '.wav', '.aac', '.ogg']:
                self.show_message("警告", "该文件不是支持的音频格式", "warning")
                return

            # 创建临时的歌曲数据
            song_name = os.path.splitext(filename)[0]
            # 尝试从文件名中提取艺术家信息
            if ' - ' in song_name:
                artist_part, name_part = song_name.split(' - ', 1)
                song_name = name_part
                artist_name = artist_part
            else:
                artist_name = '本地文件'
            
            song_data = {
                'name': song_name,
                'artist': artist_name,
                'album': '下载文件夹',
                'source': 'local',
                'local_path': filepath
            }

            # 在主程序中播放
            if hasattr(self.main_app, 'play_local_file'):
                self.main_app.play_local_file(song_data, filepath)

            self.log(f"播放本地文件: {filename}")
        else:
            self.show_message("错误", "文件不存在", "error")

    def delete_downloaded_file(self):
        """删除下载的文件"""
        selection = self.download_tree.selection()
        if not selection:
            self.show_message("警告", "请先选择一个文件", "warning")
            return

        if not self.show_message("确认", "确定要删除选中的文件吗？", "ask"):
            return

        deleted_count = 0
        for item in selection:
            values = self.download_tree.item(item, 'values')
            if values:
                filename = values[0]
                folder = self.download_path
                filepath = os.path.join(folder, filename)

                try:
                    os.remove(filepath)
                    self.download_tree.delete(item)
                    deleted_count += 1
                    self.log(f"已删除文件: {filename}")
                except Exception as e:
                    self.log(f"删除文件失败 {filename}: {str(e)}", "ERROR")

        if deleted_count > 0:
            self.show_message("成功", f"已删除 {deleted_count} 个文件", "info")
            self.refresh_downloads()

    def clear_download_history(self):
        """清除下载历史（仅清除显示，不删除文件）"""
        if not self.show_message("确认", "确定要清除下载历史记录吗？（不会删除文件）", "ask"):
            return

        # 清空树状视图
        for item in self.download_tree.get_children():
            self.download_tree.delete(item)

        # 重置统计
        self.stats_label.config(text="文件数: 0 | 总大小: 0MB")

        self.log("下载历史记录已清除")

    def _format_file_size(self, size_bytes):
        """格式化文件大小显示"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f}KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes/(1024*1024):.1f}MB"
        else:
            return f"{size_bytes/(1024*1024*1024):.1f}GB"

    def _save_download_history(self):
        """保存下载历史到文件"""
        try:
            history_file = os.path.join(self.download_path, "download_history.json")

            # 确保目录存在
            os.makedirs(os.path.dirname(history_file), exist_ok=True)

            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.download_history, f, ensure_ascii=False, indent=2)

            self.log(f"下载历史已保存到: {history_file}")

        except Exception as e:
            self.log(f"保存下载历史失败: {str(e)}", "ERROR")

    def _load_download_history(self):
        """加载下载历史"""
        try:
            history_file = os.path.join(self.download_path, "download_history.json")
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.download_history = json.load(f)
                self.log(f"加载下载历史，共 {len(self.download_history)} 条记录")
            else:
                self.log("下载历史文件不存在，创建新文件")
                # 创建空的历史文件
                self._save_download_history()
        except Exception as e:
            self.log(f"加载下载历史失败: {str(e)}", "ERROR")
            self.download_history = []

    def _format_artist(self, artist_data):
        """格式化艺术家信息"""
        if isinstance(artist_data, list):
            artist_names = []
            for artist in artist_data:
                if isinstance(artist, dict):
                    artist_names.append(artist.get('name', ''))
                elif isinstance(artist, str):
                    artist_names.append(artist)
            return ' / '.join([a for a in artist_names if a])
        elif isinstance(artist_data, str):
            return artist_data
        else:
            return str(artist_data)