import requests
import json
import time
from typing import Optional, List, Dict, Any

class MusicAPI:
    """音乐API封装类"""
    
    def __init__(self, base_url: str = "https://music-api.gdstudio.xyz/api.php"):
        self.base_url = base_url
        self.last_request_time = 0
        self.request_interval = 1.0  # 请求间隔，避免超过频率限制
    
    def _make_request(self, params: Dict) -> Optional[Any]:
        """发送API请求"""
        # 控制请求频率
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_interval:
            time.sleep(self.request_interval - time_since_last)
        
        try:
            self.log(f"发送请求: {params}")
            response = requests.get(self.base_url, params=params, timeout=15)
            self.last_request_time = time.time()
            
            self.log(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"响应数据: {json.dumps(data, ensure_ascii=False)[:100]}...")
                return data
            else:
                self.log(f"API请求失败: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"网络请求错误: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            self.log(f"JSON解析错误: {str(e)}")
            return None
    
    def search(self, keyword: str, source: str = "netease", 
               page: int = 1, count: int = 20) -> Optional[List[Dict]]:
        """搜索音乐"""
        params = {
            'types': 'search',
            'source': source,
            'name': keyword,
            'count': count,
            'pages': page
        }
        return self._make_request(params)
    
    def get_play_url(self, song_id: str, source: str = "netease", 
                     quality: str = "320") -> Optional[Dict]:
        """获取播放链接"""
        # 需要确保song_id是字符串
        if isinstance(song_id, (int, float)):
            song_id = str(int(song_id))
        
        params = {
            'types': 'url',
            'source': source,
            'id': song_id,
            'br': quality
        }
        return self._make_request(params)
    
    def get_lyric(self, lyric_id: str, source: str = "netease") -> Optional[Dict]:
        """获取歌词"""
        params = {
            'types': 'lyric',
            'source': source,
            'id': lyric_id
        }
        return self._make_request(params)
    
    def get_album_pic(self, pic_id: str, source: str = "netease", 
                      size: int = 500) -> Optional[Dict]:
        """获取专辑图"""
        params = {
            'types': 'pic',
            'source': source,
            'id': pic_id,
            'size': size
        }
        return self._make_request(params)
    
    def log(self, message: str):
        """日志记录"""
        print(f"[MusicAPI] {message}")