# gui/main_window.py (修复初始化部分)
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
import copy
import traceback

from .enhanced_player_window import EnhancedPlayerWindow
from .search_panel import SearchPanel
from .favorites_panel import FavoritesPanel
from .playlist_panel import PlaylistPanel
from .downloads_panel import DownloadsPanel

from api.music_api import MusicAPI
from utils.file_handler import FileHandler
from utils.playlist_handler import PlaylistHandler
from utils.logger import Logger
from utils.download_manager import DownloadManager

class MainWindow:
    """主窗口控制器"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("GD音乐播放器")
        self.root.geometry("1200x800")
        
        # 设置窗口关闭协议
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 标记窗口是否已关闭
        self.window_closed = False
        
        # 初始化核心组件
        self.api = MusicAPI()
        self.file_handler = FileHandler()
        self.playlist_handler = PlaylistHandler()
        self.logger = Logger()
        
        # 数据存储
        self.favorites = []
        self.playlist = []  # 当前播放列表
        
        # 初始化UI控件引用
        self.tab_control = None
        self.player_window = None
        self.search_panel = None
        self.favorites_panel = None
        self.playlist_panel = None
        self.downloads_panel = None
        
        # 下载相关变量
        self.download_path = "downloads/"
        self.download_manager = DownloadManager(self.download_path)
        
        # 设置下载回调
        self.download_manager.on_download_start = self._on_download_start
        self.download_manager.on_download_progress = self._on_download_progress
        self.download_manager.on_download_complete = self._on_download_complete
        self.download_manager.on_download_error = self._on_download_error
        
        try:
            # 创建界面
            self.setup_ui()
            
            # 加载数据
            self._load_favorites()
            self._load_playlist()
            
            # 刷新UI显示
            if hasattr(self, 'favorites_panel'):
                self.favorites_panel.refresh_favorites_display(self.favorites)
            if hasattr(self, 'playlist_panel'):
                self.playlist_panel.refresh_playlist_display(self.playlist)
            
            self.log("GD音乐播放器启动成功")
        except Exception as e:
            self.log(f"启动失败: {str(e)}", "ERROR")
            traceback.print_exc()
            messagebox.showerror("启动错误", f"程序启动失败:\n{str(e)}")
            self.root.destroy()
    
    def setup_ui(self):
        """设置主界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建左侧面板（搜索面板）
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 创建右侧面板（选项卡）
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 设置左侧搜索面板
        self.search_panel = SearchPanel(left_panel, self)
        self.search_panel.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 设置右侧选项卡面板
        self._setup_right_tab_panel(right_panel)
        
        # 配置左侧面板网格权重
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(0, weight=1)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
    
    def _setup_right_tab_panel(self, parent):
        """设置右侧选项卡面板"""
        # 创建笔记本（选项卡）
        self.tab_control = ttk.Notebook(parent)
        self.tab_control.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建播放器选项卡
        player_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(player_tab, text="播放器")
        self.player_window = EnhancedPlayerWindow(player_tab, self)
        self.player_window.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 设置播放列表
        self.player_window.set_playlist(self.playlist)
        
        # 创建收藏选项卡
        favorites_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(favorites_tab, text="我的收藏")
        self.favorites_panel = FavoritesPanel(favorites_tab, self)
        self.favorites_panel.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # 延迟刷新，确保数据已加载
        self.root.after(100, lambda: self.favorites_panel.refresh_favorites_display(self.favorites))
        
        # 创建播放列表选项卡
        playlist_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(playlist_tab, text="播放列表")
        self.playlist_panel = PlaylistPanel(playlist_tab, self)
        self.playlist_panel.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # 延迟刷新，确保数据已加载
        self.root.after(100, lambda: self.playlist_panel.refresh_playlist_display(self.playlist))
        
        # 创建下载管理选项卡
        downloads_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(downloads_tab, text="下载管理")
        self.downloads_panel = DownloadsPanel(downloads_tab, self)
        self.downloads_panel.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        
        # 为每个选项卡配置网格权重
        for tab in [player_tab, favorites_tab, playlist_tab, downloads_tab]:
            tab.rowconfigure(0, weight=1)
            tab.columnconfigure(0, weight=1)
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        try:
            self.logger.log(message, level)
            # 同时更新搜索面板的日志（仅在UI存在时）
            if (hasattr(self, 'search_panel') and hasattr(self.search_panel, 'log_text') and 
                hasattr(self, 'root') and self.root and not self.window_closed):
                # 获取时间戳
                from datetime import datetime
                timestamp = datetime.now().strftime("%H:%M:%S")
                log_message = f"[{timestamp}] [{level}] {message}\n"
                
                # 安全地更新UI
                try:
                    if self.root.winfo_exists():
                        self.search_panel.log_text.insert(tk.END, log_message)
                        self.search_panel.log_text.see(tk.END)
                        self.search_panel.log_text.update_idletasks()
                except Exception:
                    # 如果UI更新失败，只打印到控制台
                    print(f"[UI更新失败] {log_message.strip()}")
        except Exception:
            # 如果日志记录失败，只打印到控制台
            print(f"[{level}] {message}")
    
    # ========== 数据管理方法 ==========
    
    def get_favorites(self):
        """获取收藏列表"""
        return self.favorites
    
    def get_playlist(self):
        """获取播放列表"""
        return self.playlist
    
    def get_playlist_song_at_index(self, index):
        """获取播放列表中指定索引的歌曲"""
        if 0 <= index < len(self.playlist):
            return self.playlist[index]
        return None
    
    # ========== 收藏管理 ==========
    
    def _load_favorites(self):
        """加载收藏列表"""
        try:
            self.favorites = self.file_handler.load_favorites()
            self.log(f"加载收藏列表，共 {len(self.favorites)} 首歌曲")
            
        except Exception as e:
            self.log(f"加载收藏失败: {str(e)}", "ERROR")
            self.favorites = []
    
    def save_favorites(self):
        """保存收藏列表"""
        if self.window_closed:
            return
            
        try:
            self.file_handler.save_favorites(self.favorites)
            self.log("收藏列表已保存")
        except Exception as e:
            self.log(f"保存收藏失败: {str(e)}", "ERROR")
    
    def add_song_to_favorites(self, song_data):
        """添加歌曲到收藏"""
        # 避免重复添加
        song_id = song_data.get('id', '')
        if not any(fav.get('id') == song_id for fav in self.favorites):
            # 深拷贝歌曲数据
            song_copy = copy.deepcopy(song_data)
            
            # 确保有source字段
            if 'source' not in song_copy:
                if hasattr(self, 'search_panel') and hasattr(self.search_panel, 'search_type'):
                    song_copy['source'] = self.search_panel.search_type.get()
                else:
                    song_copy['source'] = "netease"
            
            self.favorites.append(song_copy)
            self.save_favorites()
            
            # 刷新收藏面板显示
            if hasattr(self, 'favorites_panel') and self.root and not self.window_closed:
                if self.root.winfo_exists():
                    self.root.after(0, lambda: self.favorites_panel.refresh_favorites_display(self.favorites))
            
            return True
        return False
    
    def remove_songs_from_favorites(self, songs_to_remove):
        """从收藏中移除歌曲"""
        removed_count = 0
        songs_to_remove_ids = [song.get('id', '') for song in songs_to_remove]
        
        # 过滤掉要移除的歌曲
        self.favorites = [fav for fav in self.favorites if fav.get('id') not in songs_to_remove_ids]
        removed_count = len(songs_to_remove_ids) - len(self.favorites)
        
        if removed_count > 0:
            self.save_favorites()
            
            # 刷新收藏面板显示
            if hasattr(self, 'favorites_panel') and self.root and not self.window_closed:
                if self.root.winfo_exists():
                    self.root.after(0, lambda: self.favorites_panel.refresh_favorites_display(self.favorites))
        
        return removed_count
    
    def clear_all_favorites(self):
        """清空所有收藏"""
        self.favorites.clear()
        self.save_favorites()
        self.log("已清空所有收藏")
        
        # 刷新收藏面板显示
        if hasattr(self, 'favorites_panel') and self.root and not self.window_closed:
            if self.root.winfo_exists():
                self.root.after(0, lambda: self.favorites_panel.refresh_favorites_display(self.favorites))
    
    # ========== 播放列表管理 ==========
    
    def _load_playlist(self):
        """加载播放列表"""
        try:
            self.playlist = self.playlist_handler.load_playlist()
            self.log(f"加载播放列表，共 {len(self.playlist)} 首歌曲")
            
        except Exception as e:
            self.log(f"加载播放列表失败: {str(e)}", "ERROR")
            self.playlist = []
    
    def save_playlist(self):
        """保存播放列表"""
        if self.window_closed:
            return
            
        try:
            self.playlist_handler.save_playlist(self.playlist)
            self.log("播放列表已保存")
        except Exception as e:
            self.log(f"保存播放列表失败: {str(e)}", "ERROR")
    
    def add_song_to_playlist(self, song_data):
        """添加歌曲到播放列表"""
        # 避免重复添加
        song_id = song_data.get('id', '')
        if not any(song.get('id') == song_id for song in self.playlist):
            # 深拷贝歌曲数据
            song_copy = copy.deepcopy(song_data)
            
            # 确保有source字段
            if 'source' not in song_copy:
                if hasattr(self, 'search_panel') and hasattr(self.search_panel, 'search_type'):
                    song_copy['source'] = self.search_panel.search_type.get()
                else:
                    song_copy['source'] = "netease"
            
            self.playlist.append(song_copy)
            self.save_playlist()
            
            # 更新播放器窗口的播放列表
            if hasattr(self, 'player_window'):
                self.player_window.add_to_playlist(song_copy)
            
            # 刷新播放列表面板显示
            if hasattr(self, 'playlist_panel') and self.root and not self.window_closed:
                if self.root.winfo_exists():
                    self.root.after(0, lambda: self.playlist_panel.refresh_playlist_display(self.playlist))
            
            return True
        return False
    
    def remove_songs_from_playlist(self, indices):
        """从播放列表中移除歌曲"""
        try:
            # 从后往前移除，避免索引变化
            removed_songs = []
            for idx in sorted(indices, reverse=True):
                if 0 <= idx < len(self.playlist):
                    removed_songs.append(self.playlist.pop(idx))
            
            if removed_songs:
                self.save_playlist()
                
                # 重新设置播放器窗口的播放列表
                if hasattr(self, 'player_window'):
                    self.player_window.set_playlist(self.playlist)
                
                # 刷新播放列表面板显示
                if hasattr(self, 'playlist_panel') and self.root and not self.window_closed:
                    if self.root.winfo_exists():
                        self.root.after(0, lambda: self.playlist_panel.refresh_playlist_display(self.playlist))
            
            return True
        except Exception as e:
            self.log(f"移除播放列表歌曲失败: {str(e)}", "ERROR")
            return False
    
    def clear_playlist(self):
        """清空播放列表"""
        self.playlist.clear()
        self.save_playlist()
        self.log("已清空播放列表")
        
        # 重新设置播放器窗口的播放列表
        if hasattr(self, 'player_window'):
            self.player_window.clear_playlist()
        
        # 刷新播放列表面板显示
        if hasattr(self, 'playlist_panel') and self.root and not self.window_closed:
            if self.root.winfo_exists():
                self.root.after(0, lambda: self.playlist_panel.refresh_playlist_display(self.playlist))
    
    def load_playlist_from_file(self, filename):
        """从文件加载播放列表"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                loaded_playlist = json.load(f)
            
            # 清空当前播放列表
            self.playlist.clear()
            self.playlist.extend(loaded_playlist)
            self.save_playlist()
            
            # 重新设置播放器窗口的播放列表
            if hasattr(self, 'player_window'):
                self.player_window.set_playlist(self.playlist)
            
            # 刷新播放列表面板显示
            if hasattr(self, 'playlist_panel') and self.root and not self.window_closed:
                if self.root.winfo_exists():
                    self.root.after(0, lambda: self.playlist_panel.refresh_playlist_display(self.playlist))
            
            self.log(f"播放列表已加载: {filename}，共 {len(self.playlist)} 首歌曲")
            return True
            
        except Exception as e:
            self.log(f"加载播放列表失败: {str(e)}", "ERROR")
            return False
    
    # ========== 搜索功能 ==========
    
    def search_music(self, keyword, source, search_panel):
        """搜索音乐"""
        def search_thread():
            try:
                results = self.api.search(keyword, source)
                
                if results and len(results) > 0:
                    # 使用安全的方式在主线程中更新UI
                    if self.root and not self.window_closed and self.root.winfo_exists():
                        self.root.after(0, lambda: self._update_search_results(results, source, search_panel))
                else:
                    # 没有结果
                    if self.root and not self.window_closed and self.root.winfo_exists():
                        self.root.after(0, lambda: messagebox.showinfo("提示", "未找到相关歌曲"))
                    
            except Exception as e:
                # 记录错误，但不尝试在主线程中显示消息（因为主线程可能已经退出）
                error_msg = str(e)
                self.log(f"搜索失败: {error_msg}", "ERROR")
                # 避免在主线程已经退出时调用after方法
                if self.root and not self.window_closed and self.root.winfo_exists():
                    self.root.after(0, lambda: messagebox.showerror("错误", f"搜索失败: {error_msg}"))
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def _update_search_results(self, results, source, search_panel):
        """安全地更新搜索结果"""
        try:
            if hasattr(search_panel, 'display_search_results'):
                search_panel.display_search_results(results, source)
                self.log(f"找到 {len(results)} 首歌曲")
        except Exception as e:
            self.log(f"显示搜索结果失败: {str(e)}", "ERROR")
    
    # ========== 播放功能 ==========
    
    def play_song_from_data(self, song_id, song_data, source, quality):
        """播放歌曲 - 修复：确保歌曲添加到播放列表"""
        def play_thread():
            try:
                # 获取播放链接
                url_data = self.api.get_play_url(song_id, source, quality)
                
                if url_data and isinstance(url_data, dict):
                    play_url = url_data.get('url', '')
                    
                    if play_url:
                        def play_song():
                            try:
                                # 关键修复：先添加到播放列表
                                self.add_song_to_playlist(song_data)
                                
                                # 然后播放
                                self.player_window.play_song(song_data, play_url)
                                self.log(f"开始播放: {song_data.get('name', '未知歌曲')}")
                                
                                # 显示歌曲信息
                                self._show_song_info(song_data, url_data)
                                
                                # 切换到播放器选项卡
                                if hasattr(self, 'tab_control'):
                                    self.tab_control.select(0)
                            except Exception as e:
                                self.log(f"播放失败: {str(e)}", "ERROR")
                                if self.root and not self.window_closed and self.root.winfo_exists():
                                    messagebox.showerror("错误", f"播放失败: {str(e)}")
                        
                        if self.root and not self.window_closed and self.root.winfo_exists():
                            self.root.after(0, play_song)
                    else:
                        def show_no_url():
                            self.log("未获取到播放链接", "ERROR")
                            if self.root and not self.window_closed and self.root.winfo_exists():
                                messagebox.showerror("错误", "未获取到播放链接")
                        
                        if self.root and not self.window_closed and self.root.winfo_exists():
                            self.root.after(0, show_no_url)
                else:
                    def show_failed():
                        self.log("获取播放链接失败", "ERROR")
                        if self.root and not self.window_closed and self.root.winfo_exists():
                            messagebox.showerror("错误", "获取播放链接失败")
                    
                    if self.root and not self.window_closed and self.root.winfo_exists():
                        self.root.after(0, show_failed)
                        
            except Exception as e:
                self.log(f"播放失败: {str(e)}", "ERROR")
                def show_error():
                    if self.root and not self.window_closed and self.root.winfo_exists():
                        messagebox.showerror("错误", f"播放失败: {str(e)}")
                
                if self.root and not self.window_closed and self.root.winfo_exists():
                    self.root.after(0, show_error)
        
        threading.Thread(target=play_thread, daemon=True).start()
    
    def play_song_from_playlist(self, song_data):
        """从播放列表播放歌曲"""
        def play_thread():
            try:
                song_id = song_data.get('id', '')
                source = song_data.get('source', 'netease')
                
                # 获取音质设置
                quality = "320"
                if hasattr(self, 'search_panel') and hasattr(self.search_panel, 'quality_combo'):
                    quality = self.search_panel.quality_combo.get()
                
                # 获取播放链接
                url_data = self.api.get_play_url(song_id, source, quality)
                
                if url_data and isinstance(url_data, dict):
                    play_url = url_data.get('url', '')
                    
                    if play_url:
                        def play_song():
                            try:
                                # 使用播放器窗口的play_song方法
                                self.player_window.play_song(song_data, play_url)
                                self.log(f"播放播放列表歌曲: {song_data.get('name', '未知歌曲')}")
                                
                                # 显示歌曲信息
                                self._show_song_info(song_data, url_data)
                                
                                # 切换到播放器选项卡
                                if hasattr(self, 'tab_control'):
                                    self.tab_control.select(0)
                            except Exception as e:
                                self.log(f"播放失败: {str(e)}", "ERROR")
                                if self.root and not self.window_closed and self.root.winfo_exists():
                                    messagebox.showerror("错误", f"播放失败: {str(e)}")
                        
                        if self.root and not self.window_closed and self.root.winfo_exists():
                            self.root.after(0, play_song)
                    else:
                        def show_no_url():
                            self.log("未获取到播放链接", "ERROR")
                            if self.root and not self.window_closed and self.root.winfo_exists():
                                messagebox.showerror("错误", "未获取到播放链接")
                        
                        if self.root and not self.window_closed and self.root.winfo_exists():
                            self.root.after(0, show_no_url)
                else:
                    def show_failed():
                        self.log("获取播放链接失败", "ERROR")
                        if self.root and not self.window_closed and self.root.winfo_exists():
                            messagebox.showerror("错误", "获取播放链接失败")
                    
                    if self.root and not self.window_closed and self.root.winfo_exists():
                        self.root.after(0, show_failed)
                        
            except Exception as e:
                self.log(f"播放失败: {str(e)}", "ERROR")
                def show_error():
                    if self.root and not self.window_closed and self.root.winfo_exists():
                        messagebox.showerror("错误", f"播放失败: {str(e)}")
                
                if self.root and not self.window_closed and self.root.winfo_exists():
                    self.root.after(0, show_error)
        
        threading.Thread(target=play_thread, daemon=True).start()
    
    def play_song_from_playlist_by_index(self, index):
        """通过索引从播放列表播放歌曲"""
        if 0 <= index < len(self.playlist):
            song_data = self.playlist[index]
            self.play_song_from_playlist(song_data)
        else:
            self.log(f"播放列表索引错误: {index}")
            if self.root and not self.window_closed and self.root.winfo_exists():
                messagebox.showerror("错误", f"播放列表索引错误: {index}")
    
    def play_local_file(self, song_data, filepath):
        """播放本地文件"""
        def play_in_thread():
            try:
                # 在主线程中更新播放器
                def update_player():
                    try:
                        # 直接使用播放器窗口的play_song方法
                        self.player_window.play_song(song_data, filepath)
                        self.log(f"播放本地文件: {song_data.get('name', '未知歌曲')}")
                        
                        # 显示歌曲信息
                        self._show_local_file_info(song_data, filepath)
                        
                        # 切换到播放器选项卡
                        if hasattr(self, 'tab_control'):
                            self.tab_control.select(0)
                    except Exception as e:
                        self.log(f"播放本地文件失败: {str(e)}", "ERROR")
                        if self.root and not self.window_closed and self.root.winfo_exists():
                            messagebox.showerror("错误", f"播放本地文件失败: {str(e)}")
                
                if self.root and not self.window_closed and self.root.winfo_exists():
                    self.root.after(0, update_player)
                    
            except Exception as e:
                self.log(f"播放本地文件失败: {str(e)}", "ERROR")
                if self.root and not self.window_closed and self.root.winfo_exists():
                    messagebox.showerror("错误", f"播放本地文件失败: {str(e)}")
        
        threading.Thread(target=play_in_thread, daemon=True).start()
    
    def _show_song_info(self, song_data, url_data):
        """显示歌曲信息"""
        if hasattr(self, 'search_panel') and hasattr(self.search_panel, 'info_text'):
            info = f"歌曲: {song_data.get('name', '未知歌曲')}\n"
            
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
            
            info += f"艺术家: {artist_name}\n"
            info += f"专辑: {song_data.get('album', '未知专辑')}\n"
            
            if url_data:
                info += f"音质: {url_data.get('br', '未知')}kbps\n"
                info += f"文件大小: {url_data.get('size', '未知')}KB\n"
            
            if self.root and not self.window_closed and self.root.winfo_exists():
                self.search_panel.info_text.delete(1.0, tk.END)
                self.search_panel.info_text.insert(1.0, info)
    
    def _show_local_file_info(self, song_data, filepath):
        """显示本地文件信息"""
        if hasattr(self, 'search_panel') and hasattr(self.search_panel, 'info_text'):
            info = f"歌曲: {song_data.get('name', '未知歌曲')}\n"
            info += f"艺术家: {song_data.get('artist', '未知艺术家')}\n"
            info += f"来源: 本地文件\n"
            info += f"路径: {filepath}\n"
            
            # 获取文件大小
            try:
                size = os.path.getsize(filepath)
                size_str = self._format_file_size(size)
                info += f"文件大小: {size_str}\n"
            except:
                pass
            
            if self.root and not self.window_closed and self.root.winfo_exists():
                self.search_panel.info_text.delete(1.0, tk.END)
                self.search_panel.info_text.insert(1.0, info)
    
    def _format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f}KB"
        else:
            return f"{size_bytes/(1024*1024):.1f}MB"
    
    # ========== 下载功能 ==========
    
    def download_song(self, song_id, song_data, source, quality):
        """下载歌曲"""
        self.log(f"开始下载: {song_data.get('name', '未知歌曲')}")
        
        # 添加到下载队列
        download_item = self.download_manager.add_to_queue(song_data, source, quality)
        
        # 更新下载管理面板（如果存在）
        if hasattr(self, 'downloads_panel') and self.downloads_panel:
            self.downloads_panel.update_download_queue()
    
    def get_download_queue(self):
        """获取下载队列"""
        return self.download_manager.get_download_queue()
    
    def get_download_history(self):
        """获取下载历史"""
        return self.download_manager.get_download_history()
    
    def cancel_download(self, download_id):
        """取消下载"""
        return self.download_manager.remove_from_queue(download_id)
    
    def cancel_all_downloads(self):
        """取消所有下载"""
        self.download_manager.cancel_all_downloads()
    
    def _on_download_start(self, download_item):
        """下载开始回调"""
        def update_ui():
            self.log(f"开始下载: {download_item['name']}")
            if hasattr(self, 'downloads_panel') and self.downloads_panel:
                self.downloads_panel.update_download_queue()
        
        if self.root and not self.window_closed and self.root.winfo_exists():
            self.root.after(0, update_ui)
    
    def _on_download_progress(self, download_item):
        """下载进度回调"""
        def update_ui():
            if hasattr(self, 'downloads_panel') and self.downloads_panel:
                self.downloads_panel.update_download_progress(download_item)
        
        if self.root and not self.window_closed and self.root.winfo_exists():
            self.root.after(0, update_ui)
    
    def _on_download_complete(self, download_item):
        """下载完成回调"""
        def update_ui():
            self.log(f"下载完成: {download_item['name']}")
            if hasattr(self, 'downloads_panel') and self.downloads_panel:
                self.downloads_panel.update_download_queue()
                self.downloads_panel.refresh_downloads()
            
            # 显示完成消息
            if self.root and not self.window_closed and self.root.winfo_exists():
                messagebox.showinfo("下载完成", f"'{download_item['name']}' 下载完成！")
        
        if self.root and not self.window_closed and self.root.winfo_exists():
            self.root.after(0, update_ui)
    
    def _on_download_error(self, download_item, error_msg):
        """下载错误回调"""
        def update_ui():
            self.log(f"下载失败: {download_item['name']} - {error_msg}", "ERROR")
            if hasattr(self, 'downloads_panel') and self.downloads_panel:
                self.downloads_panel.update_download_queue()
            
            # 显示错误消息
            if self.root and not self.window_closed and self.root.winfo_exists():
                messagebox.showerror("下载失败", f"'{download_item['name']}' 下载失败: {error_msg}")
        
        if self.root and not self.window_closed and self.root.winfo_exists():
            self.root.after(0, update_ui)
    
    # ========== 窗口关闭处理 ==========
    
    def on_closing(self):
        """处理窗口关闭事件"""
        # 防止重复调用
        if self.window_closed:
            return
            
        self.window_closed = True
        self.log("正在关闭应用程序...")
        
        try:
            # 保存收藏
            self.save_favorites()
            
            # 保存播放列表
            self.save_playlist()
            
            # 停止播放
            if hasattr(self, 'player_window') and self.player_window:
                try:
                    self.player_window.stop()
                except:
                    pass
            
            self.log("应用程序关闭")
            
            # 标记窗口为关闭状态
            self.window_closed = True
            
            # 延迟销毁窗口，确保所有操作完成
            if self.root and self.root.winfo_exists():
                self.root.after(100, self.root.destroy)
            else:
                # 如果窗口已经销毁，直接退出
                import sys
                sys.exit(0)
                
        except Exception as e:
            self.log(f"关闭过程中出错: {str(e)}", "ERROR")
            # 无论如何都要尝试销毁窗口
            try:
                if self.root and self.root.winfo_exists():
                    self.root.destroy()
            except:
                pass