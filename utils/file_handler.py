import os
import json
import sys
from typing import List, Dict

class FileHandler:
    """文件处理工具类"""
    
    @staticmethod
    def _is_packaged():
        """检查是否在打包环境中运行"""
        return getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS')
    
    @staticmethod
    def _get_app_data_dir():
        """获取应用程序数据目录（跨平台）"""
        if sys.platform == "win32":
            # Windows: C:\Users\用户名\AppData\Roaming\GDMusicPlayer
            base_dir = os.path.join(os.getenv('APPDATA'), "GDMusicPlayer")
        elif sys.platform == "darwin":
            # macOS: ~/Library/Application Support/GDMusicPlayer
            base_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "GDMusicPlayer")
        else:
            # Linux: ~/.config/GDMusicPlayer
            base_dir = os.path.join(os.path.expanduser("~"), ".config", "GDMusicPlayer")
        
        # 确保目录存在
        if not os.path.exists(base_dir):
            os.makedirs(base_dir, exist_ok=True)
            print(f"[FileHandler] 创建应用数据目录: {base_dir}")
        
        return base_dir
    
    @staticmethod
    def get_data_dir():
        """获取数据目录"""
        if FileHandler._is_packaged():
            # 打包环境：使用用户的应用数据目录
            base_dir = FileHandler._get_app_data_dir()
            data_dir = os.path.join(base_dir, "data")
        else:
            # 开发环境：使用项目目录
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
    
    @staticmethod
    def get_download_dir():
        """获取下载目录"""
        if FileHandler._is_packaged():
            # 打包环境：使用用户目录下的Downloads文件夹
            user_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            download_dir = os.path.join(user_downloads, "GDMusicDownloads")
        else:
            # 开发环境：使用项目目录下的downloads文件夹
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            download_dir = os.path.join(project_root, "downloads")
        
        # 确保目录存在
        if not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)
            print(f"[FileHandler] 创建下载目录: {download_dir}")
        
        return download_dir
    
    @staticmethod
    def get_playlist_path():
        """获取播放列表文件路径"""
        data_dir = FileHandler.get_data_dir()
        return os.path.join(data_dir, "playlist.json")
    
    @staticmethod
    def save_playlist(playlist: List[Dict], filename: str = None):
        """保存播放列表"""
        if filename is None:
            filename = FileHandler.get_playlist_path()
            
        try:
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(playlist, f, ensure_ascii=False, indent=2)
            print(f"[FileHandler] 播放列表保存到: {filename}")
            return True
        except Exception as e:
            print(f"[FileHandler] 保存播放列表失败: {str(e)}")
            return False
    
    @staticmethod
    def load_playlist(filename: str = None) -> List[Dict]:
        """加载播放列表"""
        if filename is None:
            filename = FileHandler.get_playlist_path()
            
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[FileHandler] 成功加载播放列表，共 {len(data)} 首歌曲")
                    return data
            else:
                print(f"[FileHandler] 播放列表文件不存在，创建空列表")
                FileHandler.save_playlist([])
        except Exception as e:
            print(f"[FileHandler] 加载播放列表失败: {str(e)}")
        return []
    
    @staticmethod
    def get_download_history_path():
        """获取下载历史文件路径"""
        data_dir = FileHandler.get_data_dir()
        return os.path.join(data_dir, "download_history.json")
    
    @staticmethod
    def save_download_history(history: List[Dict], filename: str = None):
        """保存下载历史"""
        if filename is None:
            filename = FileHandler.get_download_history_path()
            
        try:
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            print(f"[FileHandler] 下载历史保存到: {filename}")
            return True
        except Exception as e:
            print(f"[FileHandler] 保存下载历史失败: {str(e)}")
            return False
    
    @staticmethod
    def load_download_history(filename: str = None) -> List[Dict]:
        """加载下载历史"""
        if filename is None:
            filename = FileHandler.get_download_history_path()
            
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[FileHandler] 成功加载下载历史，共 {len(data)} 条记录")
                    return data
            else:
                print(f"[FileHandler] 下载历史文件不存在，创建空文件")
                FileHandler.save_download_history([])
        except Exception as e:
            print(f"[FileHandler] 加载下载历史失败: {str(e)}")
        return []