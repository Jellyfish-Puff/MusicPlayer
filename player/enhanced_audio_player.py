import pygame
import threading
import time
import os
import tempfile
import requests
from typing import Optional, Callable, List, Dict
from enum import Enum

class PlayerState(Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"

class EnhancedAudioPlayer:
    """增强音频播放器，支持播放列表"""
    
    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.current_url: Optional[str] = None
        self.current_song: Optional[Dict] = None
        self.temp_file: Optional[str] = None
        self.state = PlayerState.STOPPED
        self.volume = 0.5
        self.position = 0
        self.duration = 0
        
        # 播放列表相关
        self.playlist: List[Dict] = []  # 完整的播放列表
        self.current_playlist_index = -1  # 当前播放的歌曲在播放列表中的索引
        
        # 回调函数
        self.on_state_change: Optional[Callable] = None
        self.on_position_change: Optional[Callable] = None
        self.on_song_change: Optional[Callable] = None
        self.on_playlist_end: Optional[Callable] = None
        self.on_need_next_song: Optional[Callable] = None  # 新增：需要下一首歌曲的回调
        
        # 线程控制
        self._position_thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
        
    def set_playlist(self, playlist: List[Dict]):
        """设置播放列表"""
        self.playlist = playlist.copy()  # 使用副本避免引用问题
        self.current_playlist_index = -1
        
    def add_to_playlist(self, song: Dict):
        """添加到播放列表"""
        self.playlist.append(song.copy())  # 使用副本
        
    def clear_playlist(self):
        """清空播放列表"""
        self.playlist.clear()
        self.current_playlist_index = -1
        
    def get_current_song(self) -> Optional[Dict]:
        """获取当前播放的歌曲"""
        return self.current_song
        
    def get_playlist(self) -> List[Dict]:
        """获取播放列表"""
        return self.playlist.copy()  # 返回副本
        
    def get_current_index(self) -> int:
        """获取当前播放的索引"""
        return self.current_playlist_index
        
    def play_next(self) -> bool:
        """播放下一首"""
        if not self.playlist:
            return False
            
        if self.current_playlist_index < len(self.playlist) - 1:
            self.current_playlist_index += 1
            # 通过回调通知外部需要播放下一首
            if self.on_need_next_song:
                try:
                    self.on_need_next_song(self.current_playlist_index)
                    return True
                except Exception as e:
                    self.log(f"通知播放下一首失败: {str(e)}")
                    return False
            return False
        else:
            # 播放列表结束
            if self.on_playlist_end:
                try:
                    self.on_playlist_end()
                except Exception:
                    pass
            return False
            
    def play_previous(self) -> bool:
        """播放上一首"""
        if not self.playlist:
            return False
            
        if self.current_playlist_index > 0:
            self.current_playlist_index -= 1
            # 通过回调通知外部需要播放上一首
            if self.on_need_next_song:
                try:
                    self.on_need_next_song(self.current_playlist_index)
                    return True
                except Exception as e:
                    self.log(f"通知播放上一首失败: {str(e)}")
                    return False
            return False
        return False
            
    def play_specific(self, song_data: Dict) -> bool:
        """播放指定的歌曲"""
        # 查找歌曲在播放列表中的位置
        for i, song in enumerate(self.playlist):
            if song.get('id') == song_data.get('id'):
                self.current_playlist_index = i
                break
        else:
            # 如果不在播放列表中，添加到末尾
            self.add_to_playlist(song_data)
            self.current_playlist_index = len(self.playlist) - 1
            
        # 设置当前歌曲
        self.current_song = song_data.copy()
        
        # 通知歌曲变化
        if self.on_song_change:
            try:
                self.on_song_change(song_data)
            except Exception:
                pass
                    
        # 返回True表示可以开始播放
        return True
        
    def load(self, url: str) -> bool:
        """加载音频"""
        try:
            # 停止当前播放
            self.stop()
            
            self.log(f"开始加载音频: {url[:50]}...")
            
            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            temp_filename = os.path.join(temp_dir, f"music_temp_{hash(url)}.mp3")
            self.temp_file = temp_filename
            
            # 下载音频到临时文件
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://music.gdstudio.xyz/'
            }
            
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            
            if response.status_code == 200:
                with open(temp_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # 加载到pygame
                pygame.mixer.music.load(temp_filename)
                self.current_url = url
                self.state = PlayerState.STOPPED
                self.position = 0
                
                # 获取实际音频时长
                try:
                    from mutagen.mp3 import MP3
                    audio = MP3(temp_filename)
                    self.duration = audio.info.length
                except (ImportError, Exception):
                    # 估算时长
                    file_size = os.path.getsize(temp_filename)
                    self.duration = self._estimate_duration(file_size)
                
                # 设置音量
                pygame.mixer.music.set_volume(self.volume)
                
                self.log(f"音频加载成功，时长: {self.duration:.1f}秒")
                return True
            else:
                self.log(f"下载音频失败: HTTP {response.status_code}")
                return False
            
        except Exception as e:
            self.log(f"加载音频失败: {str(e)}")
            return False
    
    def play(self, url: Optional[str] = None) -> bool:
        """播放音频"""
        try:
            if url and url != self.current_url:
                if not self.load(url):
                    return False
            
            if self.state == PlayerState.PAUSED:
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.play()
            
            self.state = PlayerState.PLAYING
            self._stop_flag.clear()
            self._start_position_tracking()
            self._notify_state_change()
            
            self.log("开始播放")
            return True
            
        except Exception as e:
            self.log(f"播放音频失败: {str(e)}")
            return False
    
    def pause(self):
        """暂停播放"""
        if self.state == PlayerState.PLAYING:
            pygame.mixer.music.pause()
            self.state = PlayerState.PAUSED
            self._notify_state_change()
            self.log("暂停播放")
    
    def resume(self):
        """恢复播放"""
        if self.state == PlayerState.PAUSED:
            pygame.mixer.music.unpause()
            self.state = PlayerState.PLAYING
            self._notify_state_change()
            self.log("恢复播放")
    
    def stop(self):
        """停止播放"""
        self._stop_position_tracking()
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        
        self.state = PlayerState.STOPPED
        self.position = 0
        self._notify_state_change()
        
        # 清理临时文件
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
                self.temp_file = None
            except Exception as e:
                self.log(f"清理临时文件失败: {str(e)}")
        
        self.log("停止播放")
    
    def seek(self, position: float):
        """跳转到指定位置（秒）"""
        try:
            if position < 0:
                position = 0
            elif position > self.duration:
                position = self.duration
            
            # 如果正在播放，先停止位置跟踪
            if self.state == PlayerState.PLAYING:
                self._stop_flag.set()
            
            pygame.mixer.music.play(start=position)
            self.position = position
            
            # 如果之前是播放状态，恢复播放和位置跟踪
            if self.state == PlayerState.PLAYING:
                self._stop_flag.clear()
                if not self._position_thread or not self._position_thread.is_alive():
                    self._start_position_tracking()
            
            self._notify_position_change()
            self.log(f"跳转到: {position:.1f}秒")
            
        except Exception as e:
            self.log(f"跳转失败: {str(e)}")
    
    def set_volume(self, volume: float):
        """设置音量（0.0-1.0）"""
        if volume < 0:
            volume = 0
        elif volume > 1:
            volume = 1
        
        self.volume = volume
        pygame.mixer.music.set_volume(volume)
    
    def get_volume(self) -> float:
        """获取当前音量"""
        return self.volume
    
    def get_state(self) -> PlayerState:
        """获取播放状态"""
        return self.state
    
    def get_position(self) -> float:
        """获取当前播放位置"""
        return self.position
    
    def get_duration(self) -> float:
        """获取音频总时长"""
        return self.duration
    
    def load_local_file(self, filepath: str) -> bool:
        """加载本地音频文件"""
        try:
            # 停止当前播放
            self.stop()
            
            self.log(f"加载本地音频文件: {filepath}")
            
            # 直接加载到pygame
            pygame.mixer.music.load(filepath)
            self.current_url = f"file://{filepath}"
            self.state = PlayerState.STOPPED
            self.position = 0
            
            # 获取实际音频时长
            try:
                from mutagen.mp3 import MP3
                audio = MP3(filepath)
                self.duration = audio.info.length
            except (ImportError, Exception):
                # 估算时长
                file_size = os.path.getsize(filepath)
                self.duration = self._estimate_duration(file_size)
            
            # 设置音量
            pygame.mixer.music.set_volume(self.volume)
            
            self.log(f"本地音频加载成功，时长: {self.duration:.1f}秒")
            return True
            
        except Exception as e:
            self.log(f"加载本地音频失败: {str(e)}")
            return False
    
    def _estimate_duration(self, file_size: int) -> float:
        """估算时长"""
        bitrate = 320000  # 320kbps
        duration = (file_size * 8) / bitrate
        return duration if duration > 0 else 180
    
    def _start_position_tracking(self):
        """启动位置跟踪线程"""
        if self._position_thread and self._position_thread.is_alive():
            return
        
        self._stop_flag.clear()
        self._position_thread = threading.Thread(
            target=self._track_position, 
            daemon=True,
            name="PositionTracker"
        )
        self._position_thread.start()
    
    def _stop_position_tracking(self):
        """停止位置跟踪"""
        self._stop_flag.set()
        # 不调用join，避免线程死锁
    
    def _track_position(self):
        """跟踪播放位置"""
        last_update = time.time()
        
        while not self._stop_flag.is_set() and self.state == PlayerState.PLAYING:
            try:
                current_time = time.time()
                time_elapsed = current_time - last_update
                
                if pygame.mixer.music.get_busy():
                    self.position += time_elapsed
                    
                    # 防止超出总时长
                    if self.position > self.duration:
                        self.position = self.duration
                    
                    # 通知位置变化
                    if current_time - last_update >= 0.1:  # 每0.1秒更新一次
                        self._notify_position_change()
                        last_update = current_time
                else:
                    # 播放自然结束
                    if self.position >= self.duration - 0.5:  # 允许微小误差
                        self._handle_playback_finished()
                        break
                
                time.sleep(0.05)
                
            except Exception as e:
                self.log(f"位置跟踪错误: {str(e)}")
                break
    
    def _handle_playback_finished(self):
        """处理播放完成"""
        self.log("播放完成")
        # 自动播放下一首
        if not self.play_next():
            # 如果没有下一首，停止播放
            self.stop()
    
    def _notify_state_change(self):
        """通知状态变化"""
        if self.on_state_change:
            try:
                self.on_state_change(self.state)
            except Exception as e:
                self.log(f"状态变化通知失败: {str(e)}")
    
    def _notify_position_change(self):
        """通知位置变化"""
        if self.on_position_change:
            try:
                self.on_position_change(self.position, self.duration)
            except Exception as e:
                self.log(f"位置变化通知失败: {str(e)}")
    
    def log(self, message: str):
        """日志记录"""
        print(f"[EnhancedAudioPlayer] {message}")