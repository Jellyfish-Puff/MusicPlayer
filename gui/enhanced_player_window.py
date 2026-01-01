import tkinter as tk
from tkinter import ttk, messagebox
from player.enhanced_audio_player import EnhancedAudioPlayer, PlayerState

class EnhancedPlayerWindow:
    """增强音乐播放器窗口，支持播放列表"""
    
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.player = EnhancedAudioPlayer()
        
        # 设置播放器回调
        self.player.on_state_change = self._on_player_state_change
        self.player.on_position_change = self._on_player_position_change
        self.player.on_song_change = self._on_song_change
        self.player.on_playlist_end = self._on_playlist_end
        self.player.on_need_next_song = self._on_need_next_song  # 新增回调
        
        self.is_dragging = False
        self.current_song = None
        self.current_url_or_path = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置播放器界面"""
        # 创建播放器框架
        self.frame = ttk.Frame(self.parent, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 专辑封面占位符
        self.album_frame = ttk.Frame(self.frame)
        self.album_frame.grid(row=0, column=0, rowspan=3, padx=(0, 10), pady=(0, 10))
        
        self.album_label = tk.Label(self.album_frame, text="🎵", font=("Arial", 48), 
                                   width=6, height=3, relief=tk.SUNKEN)
        self.album_label.grid(row=0, column=0)
        
        # 歌曲信息
        info_frame = ttk.Frame(self.frame)
        info_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W)
        
        self.song_title = tk.Label(info_frame, text="未选择歌曲", 
                                  font=("Arial", 12, "bold"), anchor="w")
        self.song_title.grid(row=0, column=0, sticky=tk.W)
        
        self.song_artist = tk.Label(info_frame, text="未知艺术家", anchor="w")
        self.song_artist.grid(row=1, column=0, sticky=tk.W)
        
        self.song_album = tk.Label(info_frame, text="未知专辑", anchor="w")
        self.song_album.grid(row=2, column=0, sticky=tk.W)
        
        # 播放进度条
        self.progress_frame = ttk.Frame(self.frame)
        self.progress_frame.grid(row=1, column=1, columnspan=2, 
                                sticky=(tk.W, tk.E), pady=10)
        
        self.time_label = tk.Label(self.progress_frame, text="0:00 / 0:00", width=12)
        self.time_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Scale(self.progress_frame, from_=0, to=100,
                                     orient=tk.HORIZONTAL, length=300)
        self.progress_bar.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))
        self.progress_bar.bind("<ButtonPress-1>", self._on_progress_press)
        self.progress_bar.bind("<ButtonRelease-1>", self._on_progress_release)
        
        # 控制按钮
        control_frame = ttk.Frame(self.frame)
        control_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=10)
        
        # 上一首按钮
        self.prev_btn = ttk.Button(control_frame, text="⏮", width=3,
                                  command=self.play_previous)
        self.prev_btn.grid(row=0, column=0, padx=2)
        
        # 播放/暂停按钮
        self.play_btn = ttk.Button(control_frame, text="▶", width=3,
                                  command=self.toggle_play)
        self.play_btn.grid(row=0, column=1, padx=2)
        
        # 下一首按钮
        self.next_btn = ttk.Button(control_frame, text="⏭", width=3,
                                  command=self.play_next)
        self.next_btn.grid(row=0, column=2, padx=2)
        
        # 停止按钮
        self.stop_btn = ttk.Button(control_frame, text="⏹", width=3,
                                  command=self.stop)
        self.stop_btn.grid(row=0, column=3, padx=2)
        
        # 播放列表信息
        playlist_info_frame = ttk.Frame(control_frame)
        playlist_info_frame.grid(row=0, column=4, padx=(20, 0))
        
        self.playlist_info = tk.Label(playlist_info_frame, text="播放列表: 0首")
        self.playlist_info.grid(row=0, column=0)
        
        # 当前播放位置
        self.current_index_label = tk.Label(playlist_info_frame, text="当前: -")
        self.current_index_label.grid(row=0, column=1, padx=(5, 0))
        
        # 音量控制
        volume_frame = ttk.Frame(control_frame)
        volume_frame.grid(row=0, column=5, padx=(20, 0))
        
        self.volume_label = tk.Label(volume_frame, text="音量:")
        self.volume_label.grid(row=0, column=0)
        
        self.volume_slider = ttk.Scale(volume_frame, from_=0, to=100,
                                      orient=tk.HORIZONTAL, length=80)
        self.volume_slider.grid(row=0, column=1, padx=(5, 0))
        self.volume_slider.set(50)
        self.volume_slider.bind("<Motion>", self._on_volume_change)
        
        # 配置网格权重
        self.frame.columnconfigure(1, weight=1)
        self.progress_frame.columnconfigure(1, weight=1)
    
    def _on_need_next_song(self, index):
        """处理需要播放下一首/上一首的回调"""
        if self.main_app and hasattr(self.main_app, 'play_song_from_playlist_by_index'):
            self.main_app.play_song_from_playlist_by_index(index)
    
    def set_playlist(self, playlist):
        """设置播放列表"""
        self.player.set_playlist(playlist)
        self._update_playlist_info()
    
    def add_to_playlist(self, song_data):
        """添加到播放列表"""
        self.player.add_to_playlist(song_data)
        self._update_playlist_info()
    
    def clear_playlist(self):
        """清空播放列表"""
        self.player.clear_playlist()
        self._update_playlist_info()
    
    def play_song(self, song_data: dict, play_url_or_path: str):
        """播放歌曲（支持URL或本地文件路径）"""
        # 先确保歌曲在播放列表中
        if self.player.play_specific(song_data):
            self.current_song = song_data
            self.current_url_or_path = play_url_or_path
            
            # 更新UI
            self._update_song_info(song_data)
            
            # 判断是URL还是本地文件路径
            if play_url_or_path.startswith('http'):
                # 在线URL
                if self.player.load(play_url_or_path):
                    self.player.play()
            else:
                # 本地文件路径
                try:
                    # 对于本地文件，直接加载
                    self.player.load_local_file(play_url_or_path)
                    self.player.play()
                except Exception as e:
                    self.log(f"加载本地文件失败: {str(e)}")
                    messagebox.showerror("错误", f"加载本地文件失败: {str(e)}")
    
    def toggle_play(self):
        """切换播放/暂停"""
        if self.player.get_state() == PlayerState.PLAYING:
            self.player.pause()
        else:
            if self.player.get_state() == PlayerState.PAUSED:
                self.player.resume()
            elif hasattr(self, 'current_url_or_path') and self.current_url_or_path:
                self.player.play()
    
    def stop(self):
        """停止播放"""
        self.player.stop()
        self.progress_bar.set(0)
        self.time_label.config(text="0:00 / 0:00")
    
    def play_next(self):
        """播放下一首"""
        if self.player.play_next():
            self.log("正在播放下一首...")
        else:
            self.log("已经是最后一首歌曲")
            messagebox.showinfo("提示", "已经是最后一首歌曲")
    
    def play_previous(self):
        """播放上一首"""
        if self.player.play_previous():
            self.log("正在播放上一首...")
        else:
            self.log("已经是第一首歌曲")
            messagebox.showinfo("提示", "已经是第一首歌曲")
    
    def _update_song_info(self, song_data: dict):
        """更新歌曲信息"""
        song_name = song_data.get('name', '未知歌曲')
        self.song_title.config(text=song_name[:30] + "..." if len(song_name) > 30 else song_name)
        
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
        
        self.song_artist.config(text=artist_name[:40] + "..." if len(artist_name) > 40 else artist_name)
        album_name = song_data.get('album', '未知专辑')
        self.song_album.config(text=album_name[:40] + "..." if len(album_name) > 40 else album_name)
        
        # 更新播放列表信息
        current_index = self.player.get_current_index()
        total_songs = len(self.player.get_playlist())
        if current_index >= 0:
            self.current_index_label.config(text=f"当前: {current_index + 1}/{total_songs}")
    
    def _update_playlist_info(self):
        """更新播放列表信息"""
        total_songs = len(self.player.get_playlist())
        self.playlist_info.config(text=f"播放列表: {total_songs}首")
    
    def _on_song_change(self, song_data: dict):
        """处理歌曲变化"""
        # 在主线程中更新UI
        self.parent.after(0, lambda: self._update_song_info(song_data))
    
    def _on_playlist_end(self):
        """处理播放列表结束"""
        self.log("播放列表播放完毕")
    
    def _on_player_state_change(self, state: PlayerState):
        """处理播放器状态变化"""
        self._update_ui_state()
    
    def _on_player_position_change(self, position: float, duration: float):
        """处理播放位置变化"""
        if not self.is_dragging:
            if duration > 0:
                progress = (position / duration) * 100
                self.progress_bar.set(progress)
            
            pos_str = self._format_time(position)
            dur_str = self._format_time(duration)
            self.time_label.config(text=f"{pos_str} / {dur_str}")
    
    def _on_progress_press(self, event):
        """进度条按下"""
        self.is_dragging = True
    
    def _on_progress_release(self, event):
        """进度条释放"""
        self.is_dragging = False
        
        if self.player.get_duration() > 0:
            progress = self.progress_bar.get()
            position = (progress / 100) * self.player.get_duration()
            self.player.seek(position)
    
    def _on_volume_change(self, event):
        """音量变化"""
        volume = self.volume_slider.get() / 100
        self.player.set_volume(volume)
    
    def _update_ui_state(self):
        """更新UI状态"""
        state = self.player.get_state()
        
        if state == PlayerState.PLAYING:
            self.play_btn.config(text="⏸")
        else:
            self.play_btn.config(text="▶")
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """格式化时间显示"""
        if seconds <= 0:
            return "0:00"
        
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def log(self, message: str):
        """记录日志"""
        print(f"[EnhancedPlayerWindow] {message}")