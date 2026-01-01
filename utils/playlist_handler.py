import json
import os
from typing import List, Dict, Any

class PlaylistHandler:
    """播放列表文件处理工具类"""
    
    @staticmethod
    def get_data_dir():
        """获取数据目录"""
        # 项目根目录下的data文件夹
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_root, "data")
        
        # 确保目录存在
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            print(f"[PlaylistHandler] 创建数据目录: {data_dir}")
        
        return data_dir
    
    @staticmethod
    def save_playlist(playlist: List[Dict], filename: str = None):
        """保存播放列表"""
        if filename is None:
            filename = PlaylistHandler.get_default_playlist_path()
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            # 清理歌曲数据，只保存必要信息
            cleaned_playlist = []
            for song in playlist:
                clean_song = {
                    'id': song.get('id', ''),
                    'name': song.get('name', '未知歌曲'),
                    'artist': song.get('artist', []),
                    'album': song.get('album', '未知专辑'),
                    'source': song.get('source', 'netease')
                }
                cleaned_playlist.append(clean_song)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(cleaned_playlist, f, ensure_ascii=False, indent=2)
            print(f"[PlaylistHandler] 播放列表保存到: {filename}，共 {len(cleaned_playlist)} 首歌曲")
            return True
        except Exception as e:
            print(f"[PlaylistHandler] 保存播放列表失败: {str(e)}")
            return False
    
    @staticmethod
    def load_playlist(filename: str = None) -> List[Dict]:
        """加载播放列表"""
        if filename is None:
            filename = PlaylistHandler.get_default_playlist_path()
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[PlaylistHandler] 成功加载 {len(data)} 首播放列表歌曲")
                    return data
            else:
                print(f"[PlaylistHandler] 播放列表文件不存在: {filename}，返回空列表")
                # 创建空文件
                PlaylistHandler.save_playlist([])
        except Exception as e:
            print(f"[PlaylistHandler] 加载播放列表失败: {str(e)}")
        return []
    
    @staticmethod
    def get_default_playlist_path() -> str:
        """获取默认播放列表路径"""
        data_dir = PlaylistHandler.get_data_dir()
        return os.path.join(data_dir, "playlist.json")