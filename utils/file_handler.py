import os
import json
from typing import List, Dict

class FileHandler:
    """文件处理工具类"""
    
    @staticmethod
    def get_data_dir():
        """获取数据目录"""
        # 项目根目录下的data文件夹
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_root, "data")
        
        # 确保目录存在
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            print(f"[FileHandler] 创建数据目录: {data_dir}")
        
        return data_dir
    
    @staticmethod
    def get_favorites_path():
        """获取收藏文件的完整路径"""
        data_dir = FileHandler.get_data_dir()
        return os.path.join(data_dir, "favorites.json")
    
    @staticmethod
    def save_favorites(favorites: List[Dict], filename: str = None):
        """保存收藏列表"""
        if filename is None:
            filename = FileHandler.get_favorites_path()
            
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            # 只保存必要字段，避免过大
            cleaned_favorites = []
            for song in favorites:
                clean_song = {
                    'id': song.get('id', ''),
                    'name': song.get('name', '未知歌曲'),
                    'artist': song.get('artist', []),
                    'album': song.get('album', '未知专辑'),
                    'source': song.get('source', 'netease')
                }
                cleaned_favorites.append(clean_song)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(cleaned_favorites, f, ensure_ascii=False, indent=2)
            print(f"[FileHandler] 收藏保存到: {filename}，共 {len(cleaned_favorites)} 首歌曲")
            return True
        except Exception as e:
            print(f"[FileHandler] 保存收藏失败: {str(e)}")
            return False
    
    @staticmethod
    def load_favorites(filename: str = None) -> List[Dict]:
        """加载收藏列表"""
        if filename is None:
            filename = FileHandler.get_favorites_path()
            
        try:
            print(f"[FileHandler] 尝试加载收藏文件: {filename}")
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[FileHandler] 成功加载 {len(data)} 首收藏歌曲")
                    return data
            else:
                print(f"[FileHandler] 收藏文件不存在: {filename}，返回空列表")
                # 创建空文件
                FileHandler.save_favorites([])
        except Exception as e:
            print(f"[FileHandler] 加载收藏失败: {str(e)}")
        return []
    
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