import os
import json
import time
from typing import List, Dict, Any
from datetime import datetime

class FileHandler:
    """文件处理工具类"""
    
    @staticmethod
    def save_favorites(favorites: List[Dict], filename: str = "favorites.json"):
        """保存收藏列表"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(favorites, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存收藏失败: {str(e)}")
            return False
    
    @staticmethod
    def load_favorites(filename: str = "favorites.json") -> List[Dict]:
        """加载收藏列表"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载收藏失败: {str(e)}")
        return []
    
    @staticmethod
    def download_file(url: str, filename: str, 
                     progress_callback: callable = None) -> bool:
        """下载文件"""
        try:
            import requests
            
            # 创建目录
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # 下载文件
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, stream=True, timeout=60)
            
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 8192
                
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if progress_callback and total_size > 0:
                                progress = (downloaded / total_size) * 100
                                # 传递进度、总大小和已下载大小
                                progress_callback(progress, total_size, downloaded)
                
                return True
            else:
                print(f"下载失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"下载文件出错: {str(e)}")
            return False
    
    @staticmethod
    def get_safe_filename(name: str) -> str:
        """获取安全的文件名"""
        # 移除非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            name = name.replace(char, '_')
        
        # 限制长度
        if len(name) > 100:
            name = name[:100]
        
        return name
    
    @staticmethod
    def get_unique_filename(filename: str) -> str:
        """获取唯一的文件名（避免重复）"""
        if not os.path.exists(filename):
            return filename
        
        base, ext = os.path.splitext(filename)
        counter = 1
        
        while True:
            new_filename = f"{base}_{counter}{ext}"
            if not os.path.exists(new_filename):
                return new_filename
            counter += 1
    
    @staticmethod
    def get_file_info(filepath: str) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            if os.path.exists(filepath):
                stat = os.stat(filepath)
                return {
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'is_file': os.path.isfile(filepath),
                    'is_dir': os.path.isdir(filepath)
                }
        except Exception as e:
            print(f"获取文件信息失败: {str(e)}")
        
        return {}