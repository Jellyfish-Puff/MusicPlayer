# gui/__init__.py
from .main_window import MainWindow
from .enhanced_player_window import EnhancedPlayerWindow
from .search_panel import SearchPanel
from .favorites_panel import FavoritesPanel
from .playlist_panel import PlaylistPanel
from .downloads_panel import DownloadsPanel
from .base_panel import BasePanel

__all__ = [
    'MainWindow',
    'EnhancedPlayerWindow',
    'SearchPanel',
    'FavoritesPanel',
    'PlaylistPanel',
    'DownloadsPanel',
    'BasePanel'
]