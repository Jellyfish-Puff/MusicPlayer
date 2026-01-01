import tkinter as tk
from tkinter import ttk
from player.audio_player import AudioPlayer, PlayerState

class PlayerWindow:
    """音乐播放器窗口"""
    
    def __init__(self, parent):
        self.parent = parent
        self.player = AudioPlayer()
        self.current_song = None
        self.is_dragging = False
        
        # 设置播放器回调
        self.player.on_state_change = self._on_player_state_change
        self.player.on_position_change = self._on_player_position_change
        
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
        
        # 音量控制
        volume_frame = ttk.Frame(control_frame)
        volume_frame.grid(row=0, column=4, padx=(20, 0))
        
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
    
    def play_song(self, song_data: dict, play_url: str):
        """播放歌曲"""
        self.current_song = song_data
        self.current_url = play_url
        
        # 更新UI
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
        
        # 播放音乐
        if self.player.load(play_url):
            self.player.play()
    
    def toggle_play(self):
        """切换播放/暂停"""
        if self.player.get_state() == PlayerState.PLAYING:
            self.player.pause()
        else:
            if self.player.get_state() == PlayerState.PAUSED:
                self.player.resume()
            elif self.current_url:
                self.player.play()
    
    def stop(self):
        """停止播放"""
        self.player.stop()
        self.progress_bar.set(0)
        self.time_label.config(text="0:00 / 0:00")
    
    def play_previous(self):
        """播放上一首"""
        # 这里可以添加播放列表的前一首逻辑
        print("播放上一首")
    
    def play_next(self):
        """播放下一首"""
        # 这里可以添加播放列表的下一首逻辑
        print("播放下一首")
    
    def _on_player_state_change(self, state: PlayerState):
        """处理播放器状态变化"""
        self._update_ui_state()
    
    def _on_player_position_change(self, position: float, duration: float):
        """处理播放位置变化"""
        if not self.is_dragging:
            # 更新进度条
            if duration > 0:
                progress = (position / duration) * 100
                self.progress_bar.set(progress)
            
            # 更新时间显示
            pos_str = self._format_time(position)
            dur_str = self._format_time(duration)
            self.time_label.config(text=f"{pos_str} / {dur_str}")
    
    def _on_progress_press(self, event):
        """进度条按下"""
        self.is_dragging = True
        # 暂停位置更新
        if self.player:
            self.player._stop_flag.set()

    def _on_progress_release(self, event):
        """进度条释放"""
        self.is_dragging = False
        
        # 跳转到指定位置
        if self.player and self.player.get_duration() > 0:
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