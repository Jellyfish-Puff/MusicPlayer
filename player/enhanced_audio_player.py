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
        self.on_need_next_song: Optional[Callable] = None
        
        # 线程控制
        self._position_thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
        self._track_start_time = 0
        self._seek_position = 0  # 专门记录跳转位置
        
    def set_playlist(self, playlist: List[Dict]):
        """设置播放列表"""
        self.playlist = playlist.copy()
        self.current_playlist_index = -1
        
    def add_to_playlist(self, song: Dict):
        """添加到播放列表"""
        self.playlist.append(song.copy())
        
    def clear_playlist(self):
        """清空播放列表"""
        self.playlist.clear()
        self.current_playlist_index = -1
        
    def get_current_song(self) -> Optional[Dict]:
        """获取当前播放的歌曲"""
        return self.current_song
        
    def get_playlist(self) -> List[Dict]:
        """获取播放列表"""
        return self.playlist.copy()
        
    def get_current_index(self) -> int:
        """获取当前播放的索引"""
        return self.current_playlist_index
        
    def play_next(self) -> bool:
        """播放下一首"""
        if not self.playlist:
            return False
            
        if self.current_playlist_index < len(self.playlist) - 1:
            self.current_playlist_index += 1
            if self.on_need_next_song:
                try:
                    self.on_need_next_song(self.current_playlist_index)
                    return True
                except Exception as e:
                    self.log(f"通知播放下一首失败: {str(e)}")
                    return False
            return False
        else:
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
        for i, song in enumerate(self.playlist):
            if song.get('id') == song_data.get('id'):
                self.current_playlist_index = i
                break
        else:
            self.add_to_playlist(song_data)
            self.current_playlist_index = len(self.playlist) - 1
            
        self.current_song = song_data.copy()
        
        if self.on_song_change:
            try:
                self.on_song_change(song_data)
            except Exception:
                pass
                    
        return True
        
    def load(self, url: str) -> bool:
        """加载音频"""
        try:
            self.stop()
            
            self.log(f"开始加载音频: {url[:50]}...")
            
            temp_dir = tempfile.gettempdir()
            temp_filename = os.path.join(temp_dir, f"music_temp_{hash(url)}.mp3")
            self.temp_file = temp_filename
            
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
                
                pygame.mixer.music.load(temp_filename)
                self.current_url = url
                self.state = PlayerState.STOPPED
                self.position = 0
                self._seek_position = 0
                
                self.duration = self._get_audio_duration(temp_filename)
                
                pygame.mixer.music.set_volume(self.volume)
                
                self.log(f"音频加载成功，时长: {self.duration:.2f}秒")
                return True
            else:
                self.log(f"下载音频失败: HTTP {response.status_code}")
                return False
            
        except Exception as e:
            self.log(f"加载音频失败: {str(e)}")
            return False
    
    def _get_audio_duration(self, filepath: str) -> float:
        """获取音频文件的准确时长"""
        try:
            from mutagen.mp3 import MP3
            from mutagen.flac import FLAC
            from mutagen.wave import WAVE
            from mutagen.oggvorbis import OggVorbis
            from mutagen.aac import AAC
            
            file_ext = os.path.splitext(filepath)[1].lower()
            
            if file_ext == '.mp3':
                audio = MP3(filepath)
            elif file_ext == '.flac':
                audio = FLAC(filepath)
            elif file_ext == '.wav':
                audio = WAVE(filepath)
            elif file_ext == '.ogg':
                audio = OggVorbis(filepath)
            elif file_ext in ['.m4a', '.aac']:
                audio = AAC(filepath)
            else:
                try:
                    sound = pygame.mixer.Sound(filepath)
                    return sound.get_length()
                except:
                    return self._estimate_duration_from_file(filepath)
            
            return audio.info.length
        except ImportError:
            self.log("mutagen库未安装，使用估算时长")
            try:
                sound = pygame.mixer.Sound(filepath)
                return sound.get_length()
            except:
                return self._estimate_duration_from_file(filepath)
        except Exception as e:
            self.log(f"获取音频时长失败，使用估算: {str(e)}")
            return self._estimate_duration_from_file(filepath)
    
    def _estimate_duration_from_file(self, filepath: str) -> float:
        """根据文件大小估算音频时长"""
        try:
            file_size = os.path.getsize(filepath)
            file_ext = os.path.splitext(filepath)[1].lower()
            
            if file_ext == '.flac':
                bitrate = 900000
            elif file_ext in ['.m4a', '.aac']:
                bitrate = 256000
            elif file_ext == '.wav':
                bitrate = 1411200
            else:
                bitrate = 320000
            
            duration = (file_size * 8) / bitrate
            return max(60, min(duration, 600))
        except:
            return 180
    
    def play(self, url: Optional[str] = None) -> bool:
        """播放音频"""
        try:
            if url and url != self.current_url:
                if not self.load(url):
                    return False
            
            if self.state == PlayerState.PAUSED:
                pygame.mixer.music.unpause()
                self.state = PlayerState.PLAYING
            else:
                # 如果有跳转位置，从那里开始播放
                if hasattr(self, '_seek_position') and self._seek_position > 0:
                    pygame.mixer.music.play(start=self._seek_position)
                    self.position = self._seek_position
                    self._seek_position = 0
                else:
                    pygame.mixer.music.play()
                    self.position = 0
            
            self.state = PlayerState.PLAYING
            self._track_start_time = time.time() - self.position
            self._stop_flag.clear()
            self._start_position_tracking()
            self._notify_state_change()
            
            self.log(f"开始播放，总时长: {self.duration:.2f}秒")
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
            self._start_position_tracking()
            self._notify_state_change()
            self.log("恢复播放")
    
    def stop(self):
        """停止播放"""
        self._stop_position_tracking()
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        
        self.state = PlayerState.STOPPED
        self.position = 0
        self._seek_position = 0
        self._notify_state_change()
        
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
                self.temp_file = None
            except Exception as e:
                self.log(f"清理临时文件失败: {str(e)}")
        
        self.log("停止播放")

    def seek(self, position: float):
        """跳转到指定位置（秒）- 修复版"""
        try:
            if position < 0:
                position = 0
            elif position > self.duration:
                position = self.duration
            
            self.log(f"开始跳转到: {position:.1f}秒")
            
            # 记录当前状态
            was_playing = self.state == PlayerState.PLAYING
            
            # 停止位置跟踪
            self._stop_position_tracking()
            
            # 停止当前播放
            pygame.mixer.music.stop()
            
            # 关键修复：使用_seek_position记录跳转位置
            self._seek_position = position
            self.position = position
            
            # 重新加载音乐并设置位置
            if self.temp_file and os.path.exists(self.temp_file):
                pygame.mixer.music.load(self.temp_file)
            
            # 从指定位置开始播放
            pygame.mixer.music.play(start=position)
            
            # 如果不是播放状态，立即暂停
            if not was_playing:
                pygame.mixer.music.pause()
                self.state = PlayerState.PAUSED
            else:
                self.state = PlayerState.PLAYING
            
            # 重置起始时间
            self._track_start_time = time.time() - position
            
            # 重新开始位置跟踪
            if self.state == PlayerState.PLAYING:
                self._start_position_tracking()
            
            # 立即通知位置变化
            self._notify_position_change()
            
            self.log(f"跳转完成到: {position:.1f}秒，状态: {self.state.value}")
            return True
            
        except Exception as e:
            self.log(f"跳转失败: {str(e)}")
            return False
    
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
            self.stop()
            
            self.log(f"加载本地音频文件: {filepath}")
            
            pygame.mixer.music.load(filepath)
            self.current_url = f"file://{filepath}"
            self.state = PlayerState.STOPPED
            self.position = 0
            self._seek_position = 0
            
            self.duration = self._get_audio_duration(filepath)
            
            pygame.mixer.music.set_volume(self.volume)
            
            self.log(f"本地音频加载成功，时长: {self.duration:.2f}秒")
            return True
            
        except Exception as e:
            self.log(f"加载本地音频失败: {str(e)}")
            return False
    
    def _start_position_tracking(self):
        """启动位置跟踪线程"""
        if self._position_thread and self._position_thread.is_alive():
            self._stop_flag.set()
            try:
                self._position_thread.join(timeout=0.5)
            except:
                pass
        
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
    
    def _track_position(self):
        """跟踪播放位置"""
        self.log("位置跟踪线程开始运行")
        
        error_count = 0
        max_errors = 5
        
        while not self._stop_flag.is_set() and self.state == PlayerState.PLAYING:
            try:
                # 使用时间计算当前位置
                current_time = time.time()
                time_elapsed = current_time - self._track_start_time
                self.position = time_elapsed
                
                # 防止超出总时长
                if self.position > self.duration:
                    self.position = self.duration
                    self._handle_playback_finished()
                    break
                
                # 通知位置变化
                self._notify_position_change()
                
                # 检查播放是否结束
                if not pygame.mixer.music.get_busy():
                    if self.position >= self.duration - 1.0:
                        self._handle_playback_finished()
                        break
                
                time.sleep(0.1)
                error_count = 0
                
            except Exception as e:
                error_count += 1
                if error_count > max_errors:
                    self.log(f"位置跟踪发生多次错误: {str(e)}，停止跟踪")
                    break
                time.sleep(0.1)
        
        self.log("位置跟踪线程结束运行")
    
    def _handle_playback_finished(self):
        """处理播放完成"""
        self.log("播放完成")
        self.position = self.duration
        self._notify_position_change()
        
        try:
            if not self.play_next():
                self.stop()
        except Exception as e:
            self.log(f"处理播放完成时出错: {str(e)}")
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