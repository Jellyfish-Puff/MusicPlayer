import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
from .base_panel import BasePanel

class SearchPanel(BasePanel):
    """搜索音乐面板"""
    
    def setup_ui(self):
        """设置搜索界面"""
        # 搜索部分
        search_frame = ttk.LabelFrame(self.frame, text="搜索音乐", padding="10")
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
        results_frame = ttk.LabelFrame(self.frame, text="搜索结果", padding="10")
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
        self.results_tree.bind("<Double-1>", lambda e: self.on_song_double_click())
        
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
        log_frame = ttk.LabelFrame(self.frame, text="日志", padding="10")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 歌曲信息显示
        info_frame = ttk.LabelFrame(self.frame, text="歌曲信息", padding="10")
        info_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.info_text = scrolledtext.ScrolledText(info_frame, height=4, width=80)
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
        self.frame.rowconfigure(2, weight=1)
        results_frame.rowconfigure(0, weight=1)
        results_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        info_frame.columnconfigure(0, weight=1)
    
    def search_music(self):
        """搜索音乐"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            self.show_message("警告", "请输入搜索关键词", "warning")
            return
        
        source = self.search_type.get()
        
        # 清空当前结果
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.log(f"开始搜索: {keyword}")
        
        # 在主程序中搜索
        if hasattr(self.main_app, 'search_music'):
            self.main_app.search_music(keyword, source, self)
    
    def clear_results(self):
        """清空搜索结果"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.search_entry.delete(0, tk.END)
        self.info_text.delete(1.0, tk.END)
    
    def on_song_double_click(self):
        """双击歌曲播放"""
        selection = self.results_tree.selection()
        if selection:
            self.play_selected()
    
    def play_selected(self):
        """播放选中歌曲"""
        selection = self.results_tree.selection()
        if not selection:
            self.show_message("警告", "请先选择一首歌曲", "warning")
            return
        
        item = selection[0]
        tags = self.results_tree.item(item, 'tags')
        
        if tags:
            try:
                song_data = json.loads(tags[0])
                song_id = song_data.get('id', '')
                source = self.search_type.get()
                quality = self.quality_combo.get()
                
                self.log(f"播放歌曲: {song_data.get('name', '未知歌曲')}")
                
                # 在主程序中播放 - 这会自动添加到播放列表
                if hasattr(self.main_app, 'play_song_from_data'):
                    self.main_app.play_song_from_data(song_id, song_data, source, quality)
                
            except json.JSONDecodeError as e:
                self.log(f"解析歌曲数据失败: {str(e)}", "ERROR")
        else:
            self.log("未找到歌曲数据")
    
    def add_to_favorites(self):
        """添加到收藏"""
        selection = self.results_tree.selection()
        if not selection:
            self.show_message("警告", "请先选择一首歌曲", "warning")
            return
        
        added_count = 0
        
        for item in selection:
            tags = self.results_tree.item(item, 'tags')
            if tags:
                try:
                    song_data = json.loads(tags[0])
                    
                    # 在主程序中添加到收藏
                    if hasattr(self.main_app, 'add_song_to_favorites'):
                        if self.main_app.add_song_to_favorites(song_data):
                            added_count += 1
                            self.log(f"已添加到收藏: {song_data.get('name', '未知歌曲')}")
                            
                except json.JSONDecodeError as e:
                    self.log(f"解析歌曲数据失败: {str(e)}", "ERROR")
        
        if added_count > 0:
            self.show_message("成功", f"已添加 {added_count} 首歌曲到收藏", "info")
        else:
            self.show_message("提示", "没有歌曲被添加到收藏", "info")
    
    def add_to_playlist(self):
        """添加到播放列表"""
        selection = self.results_tree.selection()
        if not selection:
            self.show_message("警告", "请先选择一首歌曲", "warning")
            return
        
        added_count = 0
        
        for item in selection:
            tags = self.results_tree.item(item, 'tags')
            if tags:
                try:
                    song_data = json.loads(tags[0])
                    
                    # 在主程序中添加到播放列表
                    if hasattr(self.main_app, 'add_song_to_playlist'):
                        if self.main_app.add_song_to_playlist(song_data):
                            added_count += 1
                            self.log(f"已添加到播放列表: {song_data.get('name', '未知歌曲')}")
                            
                except json.JSONDecodeError as e:
                    self.log(f"解析歌曲数据失败: {str(e)}", "ERROR")
        
        if added_count > 0:
            self.show_message("成功", f"已添加 {added_count} 首歌曲到播放列表", "info")
        else:
            self.show_message("提示", "没有新歌曲被添加到播放列表", "info")
    
    def download_selected(self):
        """下载选中歌曲"""
        selection = self.results_tree.selection()
        if not selection:
            self.show_message("警告", "请先选择一首歌曲", "warning")
            return
        
        for item in selection:
            tags = self.results_tree.item(item, 'tags')
            if tags:
                try:
                    song_data = json.loads(tags[0])
                    song_id = song_data.get('id', '')
                    source = self.search_type.get()
                    quality = self.quality_combo.get()
                    
                    # 在主程序中下载
                    if hasattr(self.main_app, 'download_song'):
                        self.main_app.download_song(song_id, song_data, source, quality)
                    
                except json.JSONDecodeError as e:
                    self.log(f"解析歌曲数据失败: {str(e)}", "ERROR")
    
    def display_search_results(self, results, source):
        """显示搜索结果"""
        for song in results:
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
            
            # 将完整数据存储到item的tags中
            self.results_tree.item(item_id, tags=(json.dumps(song, ensure_ascii=False),))
    
    def log(self, message: str):
        """记录日志到文本控件"""
        # 这个方法由主窗口的log方法处理，这里只是占位
        pass