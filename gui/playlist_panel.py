import tkinter as tk
from tkinter import ttk, filedialog
import json
from .base_panel import BasePanel

class PlaylistPanel(BasePanel):
    """播放列表面板"""
    
    def setup_ui(self):
        """设置播放列表界面"""
        # 播放列表标题
        title_frame = ttk.Frame(self.frame, padding="10")
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(title_frame, text="当前播放列表", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W)
        
        # 播放列表
        list_frame = ttk.Frame(self.frame, padding="10")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.playlist_listbox = tk.Listbox(list_frame, height=15, width=50)
        self.playlist_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.playlist_listbox.yview)
        self.playlist_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 绑定双击事件
        self.playlist_listbox.bind("<Double-Button-1>", lambda e: self.play_selected_playlist())
        
        # 播放列表操作
        action_frame = ttk.Frame(self.frame, padding="10")
        action_frame.grid(row=2, column=0, sticky=tk.W)
        
        ttk.Button(action_frame, text="播放选中", command=self.play_selected_playlist).grid(row=0, column=0, padx=2)
        ttk.Button(action_frame, text="移除选中", command=self.remove_selected_playlist).grid(row=0, column=1, padx=2)
        ttk.Button(action_frame, text="清空列表", command=self.clear_playlist).grid(row=0, column=2, padx=2)
        ttk.Button(action_frame, text="保存列表", command=self.save_playlist).grid(row=0, column=3, padx=2)
        ttk.Button(action_frame, text="加载列表", command=self.load_playlist).grid(row=0, column=4, padx=2)
        
        # 配置网格权重
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
    
    def refresh_playlist_display(self, playlist=None):
        """刷新播放列表显示"""
        if not hasattr(self, 'playlist_listbox') or self.playlist_listbox is None:
            return
        
        # 清空当前显示
        self.playlist_listbox.delete(0, tk.END)
        
        # 使用传入的播放列表或从主程序获取
        if playlist is None:
            if hasattr(self.main_app, 'get_playlist'):
                playlist = self.main_app.get_playlist()
            else:
                playlist = []
        
        # 添加歌曲到列表
        for song in playlist:
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
        
        self.log(f"刷新播放列表显示，共 {len(playlist)} 首歌曲")
    
    def play_selected_playlist(self):
        """播放选中的播放列表歌曲"""
        if not hasattr(self, 'playlist_listbox') or self.playlist_listbox is None:
            self.show_message("警告", "播放列表未初始化", "warning")
            return
            
        selection = self.playlist_listbox.curselection()
        if not selection:
            self.show_message("警告", "请先选择一首歌曲", "warning")
            return
        
        index = selection[0]
        
        # 使用新的方法通过索引播放
        if hasattr(self.main_app, 'play_song_from_playlist_by_index'):
            self.main_app.play_song_from_playlist_by_index(index)
        else:
            # 回退到旧方法
            if hasattr(self.main_app, 'get_playlist_song_at_index'):
                song_data = self.main_app.get_playlist_song_at_index(index)
                if song_data:
                    song_id = song_data.get('id', '')
                    source = song_data.get('source', 'netease')
                    
                    # 从搜索面板获取音质设置
                    quality = "320"
                    if hasattr(self.main_app, 'search_panel') and hasattr(self.main_app.search_panel, 'quality_combo'):
                        quality = self.main_app.search_panel.quality_combo.get()
                    
                    self.log(f"播放播放列表歌曲: {song_data.get('name', '未知歌曲')}")
                    
                    # 在主程序中播放
                    if hasattr(self.main_app, 'play_song_from_data'):
                        self.main_app.play_song_from_data(song_id, song_data, source, quality)
                else:
                    self.log(f"播放列表索引错误: {index}")
                    self.show_message("错误", "播放列表数据不一致", "error")
    
    def remove_selected_playlist(self):
        """移除选中的播放列表歌曲"""
        if not hasattr(self, 'playlist_listbox') or self.playlist_listbox is None:
            self.show_message("警告", "播放列表未初始化", "warning")
            return
            
        selection = self.playlist_listbox.curselection()
        if not selection:
            self.show_message("警告", "请先选择要移除的歌曲", "warning")
            return
        
        indices = list(selection)
        
        # 从主程序移除歌曲
        if hasattr(self.main_app, 'remove_songs_from_playlist'):
            if self.main_app.remove_songs_from_playlist(indices):
                # 从后往前移除，避免索引变化
                for idx in sorted(indices, reverse=True):
                    self.playlist_listbox.delete(idx)
                
                removed_count = len(indices)
                self.log(f"已从播放列表移除 {removed_count} 首歌曲")
                self.show_message("成功", f"已移除 {removed_count} 首歌曲", "info")
    
    def clear_playlist(self):
        """清空播放列表"""
        # 获取播放列表数量
        playlist_count = self.playlist_listbox.size()
        
        if playlist_count == 0:
            self.show_message("警告", "播放列表已为空", "warning")
            return
        
        if self.show_message("确认", f"确定要清空播放列表吗？共 {playlist_count} 首歌曲", "ask"):
            # 在主程序中清空播放列表
            if hasattr(self.main_app, 'clear_playlist'):
                self.main_app.clear_playlist()
                self.playlist_listbox.delete(0, tk.END)
                self.log("已清空播放列表")
                self.show_message("成功", "已清空播放列表", "info")
    
    def save_playlist(self):
        """保存播放列表"""
        # 获取播放列表
        if hasattr(self.main_app, 'get_playlist'):
            playlist = self.main_app.get_playlist()
        else:
            playlist = []
            
        if not playlist:
            self.show_message("警告", "播放列表为空", "warning")
            return
        
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = filedialog.asksaveasfilename(
                title="保存播放列表",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
                initialfile=f"playlist_{timestamp}.json"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(playlist, f, ensure_ascii=False, indent=2)
                
                self.show_message("成功", f"播放列表已保存到: {filename}", "info")
                self.log(f"播放列表保存到: {filename}")
                
        except Exception as e:
            self.show_message("错误", f"保存失败: {str(e)}", "error")
    
    def load_playlist(self):
        """加载播放列表"""
        try:
            filename = filedialog.askopenfilename(
                title="选择播放列表文件",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            
            if filename:
                # 在主程序中加载播放列表
                if hasattr(self.main_app, 'load_playlist_from_file'):
                    success = self.main_app.load_playlist_from_file(filename)
                    if success:
                        # 刷新显示
                        self.refresh_playlist_display()
                        self.show_message("成功", f"播放列表已加载，共 {self.playlist_listbox.size()} 首歌曲", "info")
                        
        except Exception as e:
            self.show_message("错误", f"加载失败: {str(e)}", "error")