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
        
        # 下载历史列表
        history_frame = ttk.LabelFrame(self.frame, text="下载历史", padding="10")
        history_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
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
        
        # 下载操作按钮
        action_frame = ttk.Frame(history_frame)
        action_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky=tk.W)
        
        ttk.Button(action_frame, text="刷新列表", command=self.refresh_downloads).grid(row=0, column=0, padx=2)
        ttk.Button(action_frame, text="播放文件", command=self.play_downloaded_file).grid(row=0, column=1, padx=2)
        ttk.Button(action_frame, text="删除文件", command=self.delete_downloaded_file).grid(row=0, column=2, padx=2)
        ttk.Button(action_frame, text="清除历史", command=self.clear_download_history).grid(row=0, column=3, padx=2)
        
        # 下载统计
        stats_frame = ttk.Frame(self.frame)
        stats_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        self.stats_label = ttk.Label(stats_frame, text="文件数: 0 | 总大小: 0MB")
        self.stats_label.grid(row=0, column=0, sticky=tk.W)
        
        # 配置网格权重
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
        history_frame.rowconfigure(0, weight=1)
        history_frame.columnconfigure(0, weight=1)
        folder_frame.columnconfigure(1, weight=1)
        
        # 初始化下载文件夹
        self._init_download_folder()
    
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
            song_data = {
                'name': song_name,
                'artist': '本地文件',
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