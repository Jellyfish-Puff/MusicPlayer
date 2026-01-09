# utils/download_manager.py
import os
import requests
import threading
import time
import json
from datetime import datetime
from typing import Dict, List, Callable, Optional
from urllib.parse import quote

class DownloadManager:
    """下载管理器"""
    
    def __init__(self, download_path: str = "downloads/"):
        self.download_path = download_path
        self.download_queue: List[Dict] = []
        self.download_history: List[Dict] = []
        self.current_downloads: Dict[str, Dict] = {}
        self.is_downloading = False
        self.download_thread: Optional[threading.Thread] = None
        self.on_download_start: Optional[Callable] = None
        self.on_download_progress: Optional[Callable] = None
        self.on_download_complete: Optional[Callable] = None
        self.on_download_error: Optional[Callable] = None
        
        # 确保下载目录存在
        if not os.path.exists(download_path):
            os.makedirs(download_path, exist_ok=True)
    
    def add_to_queue(self, song_data: Dict, source: str = "netease", quality: str = "320"):
        """添加到下载队列"""
        download_item = {
            'id': str(song_data.get('id', '')),
            'name': song_data.get('name', '未知歌曲'),
            'artist': song_data.get('artist', []),
            'album': song_data.get('album', '未知专辑'),
            'source': source,
            'quality': quality,
            'song_data': song_data,
            'status': '等待中',
            'progress': 0,
            'added_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'start_time': None,
            'end_time': None,
            'file_path': None,
            'file_size': 0
        }
        
        self.download_queue.append(download_item)
        self.log(f"添加到下载队列: {download_item['name']}")
        
        # 如果没有正在下载，开始下载
        if not self.is_downloading:
            self.start_download()
        
        return download_item
    
    def start_download(self):
        """开始下载"""
        if self.is_downloading or not self.download_queue:
            return
        
        self.is_downloading = True
        self.download_thread = threading.Thread(target=self._download_worker, daemon=True)
        self.download_thread.start()
    
    def _download_worker(self):
        """下载工作线程"""
        while self.download_queue and self.is_downloading:
            download_item = self.download_queue.pop(0)
            
            # 更新状态为下载中
            download_item['status'] = '下载中'
            download_item['start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 生成文件名
            safe_name = self._get_safe_filename(download_item['name'])
            artist_name = self._format_artist(download_item['artist'])
            if artist_name:
                safe_name = f"{artist_name} - {safe_name}"
            
            # 添加音质后缀
            quality_map = {
                '128': '128kbps',
                '192': '192kbps',
                '320': '320kbps',
                '740': '无损',
                '999': 'Hi-Res'
            }
            quality_suffix = quality_map.get(download_item['quality'], '')
            if quality_suffix:
                safe_name = f"{safe_name} ({quality_suffix})"
            
            # 根据来源确定文件扩展名
            source = download_item['source']
            if source in ['kuwo', 'joox']:
                file_ext = '.mp3'
            elif source == 'netease':
                # 网易云通常是m4a或mp3
                if download_item['quality'] in ['740', '999']:
                    file_ext = '.flac'
                else:
                    file_ext = '.mp3'
            else:
                file_ext = '.mp3'
            
            # 如果文件已存在，添加序号
            filepath = os.path.join(self.download_path, safe_name + file_ext)
            counter = 1
            while os.path.exists(filepath):
                filepath = os.path.join(self.download_path, f"{safe_name} ({counter}){file_ext}")
                counter += 1
            
            download_item['file_path'] = filepath
            
            # 通知开始下载
            if self.on_download_start:
                try:
                    self.on_download_start(download_item)
                except:
                    pass
            
            try:
                # 通过API获取下载链接
                from api.music_api import MusicAPI
                api = MusicAPI()
                
                # 获取播放/下载链接
                url_data = api.get_play_url(
                    download_item['id'], 
                    download_item['source'], 
                    download_item['quality']
                )
                
                if not url_data or 'url' not in url_data:
                    raise Exception(f"无法获取下载链接: {download_item['name']}")
                
                download_url = url_data['url']
                self.log(f"开始下载: {download_item['name']} - {download_url[:50]}...")
                
                # 下载文件
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://music.gdstudio.xyz/'
                }
                
                response = requests.get(download_url, headers=headers, stream=True, timeout=30)
                
                if response.status_code == 200:
                    # 获取文件大小
                    total_size = int(response.headers.get('content-length', 0))
                    download_item['file_size'] = total_size
                    
                    # 写入文件
                    downloaded_size = 0
                    start_time = time.time()
                    
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                
                                # 计算进度
                                if total_size > 0:
                                    progress = (downloaded_size / total_size) * 100
                                    download_item['progress'] = progress
                                    
                                    # 计算下载速度
                                    elapsed_time = time.time() - start_time
                                    if elapsed_time > 0:
                                        speed = downloaded_size / elapsed_time / 1024  # KB/s
                                        download_item['speed'] = f"{speed:.1f} KB/s"
                                    
                                    # 通知进度更新
                                    if self.on_download_progress:
                                        try:
                                            self.on_download_progress(download_item)
                                        except:
                                            pass
                    
                    # 下载完成
                    download_item['status'] = '已完成'
                    download_item['progress'] = 100
                    download_item['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 添加到历史记录
                    self.download_history.append(download_item.copy())
                    
                    # 保存下载历史
                    self._save_download_history()
                    
                    # 通知下载完成
                    if self.on_download_complete:
                        try:
                            self.on_download_complete(download_item)
                        except:
                            pass
                    
                    self.log(f"下载完成: {download_item['name']} -> {filepath}")
                    
                else:
                    raise Exception(f"HTTP {response.status_code}: {download_item['name']}")
                
            except Exception as e:
                # 下载失败
                download_item['status'] = f'失败: {str(e)}'
                download_item['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 通知下载错误
                if self.on_download_error:
                    try:
                        self.on_download_error(download_item, str(e))
                    except:
                        pass
                
                self.log(f"下载失败: {download_item['name']} - {str(e)}", "ERROR")
        
        # 下载队列已空
        self.is_downloading = False
    
    def get_download_queue(self) -> List[Dict]:
        """获取下载队列"""
        return self.download_queue.copy()
    
    def get_download_history(self) -> List[Dict]:
        """获取下载历史"""
        return self.download_history.copy()
    
    def clear_download_history(self):
        """清空下载历史"""
        self.download_history.clear()
        self._save_download_history()
    
    def remove_from_queue(self, download_id: str):
        """从队列中移除下载任务"""
        for i, item in enumerate(self.download_queue):
            if item['id'] == download_id:
                self.download_queue.pop(i)
                self.log(f"已从队列移除: {item['name']}")
                return True
        return False
    
    def cancel_all_downloads(self):
        """取消所有下载"""
        self.download_queue.clear()
        self.is_downloading = False
        self.log("已取消所有下载任务")
    
    def _get_safe_filename(self, name: str) -> str:
        """获取安全的文件名"""
        # 移除非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            name = name.replace(char, '_')
        
        # 限制长度
        if len(name) > 100:
            name = name[:100]
        
        return name.strip()
    
    def _format_artist(self, artist_data) -> str:
        """格式化艺术家信息"""
        if isinstance(artist_data, list):
            artist_names = []
            for artist in artist_data:
                if isinstance(artist, dict):
                    artist_names.append(artist.get('name', ''))
                elif isinstance(artist, str):
                    artist_names.append(artist)
            return ' '.join([a for a in artist_names if a])
        elif isinstance(artist_data, str):
            return artist_data
        else:
            return ''
    
    def _save_download_history(self):
        """保存下载历史"""
        try:
            history_file = os.path.join(self.download_path, "download_history.json")
            
            # 只保存必要信息，避免文件过大
            simplified_history = []
            for item in self.download_history[-100:]:  # 只保留最近100条
                simplified_item = {
                    'name': item.get('name', ''),
                    'artist': item.get('artist', ''),
                    'album': item.get('album', ''),
                    'status': item.get('status', ''),
                    'file_path': item.get('file_path', ''),
                    'end_time': item.get('end_time', ''),
                    'file_size': item.get('file_size', 0)
                }
                simplified_history.append(simplified_item)
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(simplified_history, f, ensure_ascii=False, indent=2)
            
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
        except Exception as e:
            self.log(f"加载下载历史失败: {str(e)}", "ERROR")
            self.download_history = []
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        print(f"[DownloadManager] [{level}] {message}")