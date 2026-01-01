import tkinter as tk
from tkinter import ttk, filedialog
import json
from datetime import datetime
from .base_panel import BasePanel

class FavoritesPanel(BasePanel):
    """收藏管理面板"""
    
    def setup_ui(self):
        """设置收藏界面"""
        # 搜索收藏
        search_frame = ttk.Frame(self.frame, padding="5")
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(search_frame, text="搜索收藏:").grid(row=0, column=0, sticky=tk.W)
        self.fav_search_entry = ttk.Entry(search_frame, width=30)
        self.fav_search_entry.grid(row=0, column=1, padx=(5, 5))
        self.fav_search_entry.bind('<Return>', lambda e: self.search_favorites())
        
        ttk.Button(search_frame, text="搜索", command=self.search_favorites).grid(row=0, column=2, padx=2)
        ttk.Button(search_frame, text="刷新", command=self.refresh_favorites).grid(row=0, column=3, padx=2)
        
        # 收藏列表
        list_frame = ttk.LabelFrame(self.frame, text="收藏列表", padding="10")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建树状视图
        columns = ('name', 'artist', 'album', 'source')
        self.fav_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        # 定义列
        self.fav_tree.heading('name', text='歌曲名')
        self.fav_tree.heading('artist', text='艺术家')
        self.fav_tree.heading('album', text='专辑')
        self.fav_tree.heading('source', text='来源')
        
        # 设置列宽
        self.fav_tree.column('name', width=180)
        self.fav_tree.column('artist', width=100)
        self.fav_tree.column('album', width=120)
        self.fav_tree.column('source', width=60, anchor='center')
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.fav_tree.yview)
        self.fav_tree.configure(yscrollcommand=scrollbar.set)
        
        self.fav_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 绑定双击事件
        self.fav_tree.bind("<Double-1>", lambda e: self.play_selected_favorite())
        
        # 操作按钮
        fav_action_frame = ttk.Frame(list_frame)
        fav_action_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky=tk.W)
        
        ttk.Button(fav_action_frame, text="播放", command=self.play_selected_favorite).grid(row=0, column=0, padx=2)
        ttk.Button(fav_action_frame, text="下载", command=self.download_selected_favorite).grid(row=0, column=1, padx=2)
        ttk.Button(fav_action_frame, text="移除", command=self.remove_selected_favorite).grid(row=0, column=2, padx=2)
        ttk.Button(fav_action_frame, text="批量下载", command=self.batch_download_favorites).grid(row=0, column=3, padx=2)
        ttk.Button(fav_action_frame, text="导出列表", command=self.export_favorites_list).grid(row=0, column=4, padx=2)
        
        # 收藏统计信息
        stats_frame = ttk.Frame(self.frame)
        stats_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.fav_stats_label = ttk.Label(stats_frame, text="收藏数量: 0")
        self.fav_stats_label.grid(row=0, column=0, sticky=tk.W)
        
        # 批量操作
        batch_frame = ttk.Frame(self.frame)
        batch_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(batch_frame, text="全选", command=self.select_all_favorites).grid(row=0, column=0, padx=2)
        ttk.Button(batch_frame, text="反选", command=self.invert_selection_favorites).grid(row=0, column=1, padx=2)
        ttk.Button(batch_frame, text="清空收藏", command=self.clear_all_favorites).grid(row=0, column=2, padx=2)
        
        # 配置网格权重
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
    
    def refresh_favorites_display(self, favorites=None):
        """刷新收藏显示"""
        if not hasattr(self, 'fav_tree') or self.fav_tree is None:
            return
        
        # 清空当前显示
        for item in self.fav_tree.get_children():
            self.fav_tree.delete(item)
        
        # 使用传入的收藏列表或从主程序获取
        if favorites is None:
            if hasattr(self.main_app, 'get_favorites'):
                favorites = self.main_app.get_favorites()
            else:
                favorites = []
        
        # 重新加载收藏
        for song in favorites:
            name = song.get('name', '未知歌曲')
            
            # 处理艺术家信息
            artist_data = song.get('artist', [])
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
            
            album = song.get('album', '未知专辑')
            source = song.get('source', 'netease')
            
            # 来源显示
            source_map = {'netease': '网易', 'kuwo': '酷我', 'joox': 'JOOX'}
            source_str = source_map.get(source, source)
            
            # 添加到树状视图
            item_id = self.fav_tree.insert('', 'end', values=(name, artist_name, album, source_str))
            # 存储歌曲数据到item的tags中
            self.fav_tree.item(item_id, tags=(json.dumps(song, ensure_ascii=False),))
        
        # 更新统计信息
        if hasattr(self, 'fav_stats_label') and self.fav_stats_label is not None:
            self.fav_stats_label.config(text=f"收藏数量: {len(favorites)}")
        
        self.log(f"刷新收藏显示，共 {len(favorites)} 首歌曲")
    
    def search_favorites(self):
        """搜索收藏"""
        if not hasattr(self, 'fav_search_entry') or self.fav_search_entry is None:
            return
            
        keyword = self.fav_search_entry.get().strip()
        if not keyword:
            # 如果没有关键词，显示所有收藏
            self.refresh_favorites_display()
            return
        
        # 检查组件是否已初始化
        if not hasattr(self, 'fav_tree') or self.fav_tree is None:
            return
        
        # 获取收藏列表
        if hasattr(self.main_app, 'get_favorites'):
            favorites = self.main_app.get_favorites()
        else:
            favorites = []
        
        # 清空当前显示
        for item in self.fav_tree.get_children():
            self.fav_tree.delete(item)
        
        matched_count = 0
        
        # 搜索收藏
        for song in favorites:
            name = song.get('name', '')
            artist_data = song.get('artist', [])
            
            # 构建搜索文本
            search_text = name.lower()
            
            # 添加艺术家信息到搜索文本
            if isinstance(artist_data, list):
                for artist in artist_data:
                    if isinstance(artist, dict):
                        search_text += ' ' + artist.get('name', '').lower()
                    elif isinstance(artist, str):
                        search_text += ' ' + artist.lower()
            elif isinstance(artist_data, str):
                search_text += ' ' + artist_data.lower()
            
            # 添加专辑信息
            album = song.get('album', '')
            search_text += ' ' + album.lower()
            
            # 检查是否匹配
            if keyword.lower() in search_text:
                # 显示匹配的歌曲
                artist_name = ''
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
                
                album = song.get('album', '未知专辑')
                source = song.get('source', 'netease')
                
                # 来源显示
                source_map = {'netease': '网易', 'kuwo': '酷我', 'joox': 'JOOX'}
                source_str = source_map.get(source, source)
                
                # 添加到树状视图
                item_id = self.fav_tree.insert('', 'end', values=(name, artist_name, album, source_str))
                # 存储歌曲数据到item的tags中
                self.fav_tree.item(item_id, tags=(json.dumps(song, ensure_ascii=False),))
                
                matched_count += 1
        
        self.log(f"在收藏中搜索 '{keyword}'，找到 {matched_count} 首歌曲")
        if hasattr(self, 'fav_stats_label') and self.fav_stats_label is not None:
            self.fav_stats_label.config(text=f"搜索到 {matched_count} 首歌曲")
    
    def refresh_favorites(self):
        """刷新收藏列表"""
        self.refresh_favorites_display()
        self.log("收藏列表已刷新")
    
    def play_selected_favorite(self):
        """播放选中的收藏歌曲"""
        if not hasattr(self, 'fav_tree') or self.fav_tree is None:
            self.show_message("警告", "收藏列表未初始化", "warning")
            return
            
        selection = self.fav_tree.selection()
        if not selection:
            self.show_message("警告", "请先选择一首收藏歌曲", "warning")
            return
        
        item = selection[0]
        tags = self.fav_tree.item(item, 'tags')
        
        if tags:
            try:
                song_data = json.loads(tags[0])
                song_id = song_data.get('id', '')
                source = song_data.get('source', 'netease')
                
                # 从搜索面板获取音质设置
                quality = "320"
                if hasattr(self.main_app, 'search_panel') and hasattr(self.main_app.search_panel, 'quality_combo'):
                    quality = self.main_app.search_panel.quality_combo.get()
                
                self.log(f"播放收藏歌曲: {song_data.get('name', '未知歌曲')}")
                
                # 在主程序中播放 - 这会自动添加到播放列表
                if hasattr(self.main_app, 'play_song_from_data'):
                    self.main_app.play_song_from_data(song_id, song_data, source, quality)
                
            except json.JSONDecodeError as e:
                self.log(f"解析歌曲数据失败: {str(e)}", "ERROR")
    
    def download_selected_favorite(self):
        """下载选中的收藏歌曲"""
        if not hasattr(self, 'fav_tree') or self.fav_tree is None:
            return
            
        selection = self.fav_tree.selection()
        if not selection:
            self.show_message("警告", "请先选择一首收藏歌曲", "warning")
            return
        
        for item in selection:
            tags = self.fav_tree.item(item, 'tags')
            
            if tags:
                try:
                    song_data = json.loads(tags[0])
                    song_id = song_data.get('id', '')
                    source = song_data.get('source', 'netease')
                    
                    # 从搜索面板获取音质设置
                    quality = "320"
                    if hasattr(self.main_app, 'search_panel') and hasattr(self.main_app.search_panel, 'quality_combo'):
                        quality = self.main_app.search_panel.quality_combo.get()
                    
                    # 在主程序中下载
                    if hasattr(self.main_app, 'download_song'):
                        self.main_app.download_song(song_id, song_data, source, quality)
                    
                except json.JSONDecodeError as e:
                    self.log(f"解析歌曲数据失败: {str(e)}", "ERROR")
    
    def remove_selected_favorite(self):
        """移除选中的收藏歌曲"""
        if not hasattr(self, 'fav_tree') or self.fav_tree is None:
            return
            
        selection = self.fav_tree.selection()
        if not selection:
            self.show_message("警告", "请先选择要移除的歌曲", "warning")
            return
        
        # 确认删除
        if not self.show_message("确认", f"确定要移除选中的 {len(selection)} 首歌曲吗？", "ask"):
            return
        
        removed_songs = []
        
        for item in selection:
            tags = self.fav_tree.item(item, 'tags')
            
            if tags:
                try:
                    song_data = json.loads(tags[0])
                    removed_songs.append(song_data)
                    
                except json.JSONDecodeError as e:
                    self.log(f"解析歌曲数据失败: {str(e)}", "ERROR")
        
        if removed_songs and hasattr(self.main_app, 'remove_songs_from_favorites'):
            self.main_app.remove_songs_from_favorites(removed_songs)
            self.log(f"已移除 {len(removed_songs)} 首歌曲")
            self.show_message("成功", f"已移除 {len(removed_songs)} 首歌曲", "info")
        else:
            self.show_message("警告", "没有歌曲被移除", "warning")
    
    def batch_download_favorites(self):
        """批量下载收藏歌曲"""
        # 获取收藏列表
        if hasattr(self.main_app, 'get_favorites'):
            favorites = self.main_app.get_favorites()
        else:
            favorites = []
            
        if not favorites:
            self.show_message("警告", "收藏列表为空", "warning")
            return
        
        # 批量下载逻辑
        self.log("批量下载功能开发中...")
        # TODO: 实现批量下载界面和逻辑
    
    def export_favorites_list(self):
        """导出收藏列表"""
        # 获取收藏列表
        if hasattr(self.main_app, 'get_favorites'):
            favorites = self.main_app.get_favorites()
        else:
            favorites = []
            
        if not favorites:
            self.show_message("警告", "收藏列表为空", "warning")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"favorites_export_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=== 我的音乐收藏列表 ===\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"歌曲数量: {len(favorites)}\n")
                f.write("=" * 40 + "\n\n")
                
                for i, song in enumerate(favorites, 1):
                    name = song.get('name', '未知歌曲')
                    
                    # 处理艺术家信息
                    artist_data = song.get('artist', [])
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
                    
                    album = song.get('album', '未知专辑')
                    source = song.get('source', 'netease')
                    
                    f.write(f"{i:3d}. {name}\n")
                    f.write(f"     艺术家: {artist_name}\n")
                    f.write(f"     专辑: {album}\n")
                    f.write(f"     来源: {source}\n")
                    f.write(f"     歌曲ID: {song.get('id', '未知')}\n\n")
            
            self.show_message("成功", f"收藏列表已导出到: {filename}", "info")
            self.log(f"收藏列表导出到: {filename}")
            
        except Exception as e:
            self.show_message("错误", f"导出失败: {str(e)}", "error")
    
    def select_all_favorites(self):
        """全选收藏"""
        if hasattr(self, 'fav_tree') and self.fav_tree is not None:
            self.fav_tree.selection_set(self.fav_tree.get_children())
    
    def invert_selection_favorites(self):
        """反选收藏"""
        if not hasattr(self, 'fav_tree') or self.fav_tree is None:
            return
            
        all_items = set(self.fav_tree.get_children())
        selected_items = set(self.fav_tree.selection())
        
        # 计算反选后的选择
        new_selection = all_items - selected_items
        self.fav_tree.selection_set(tuple(new_selection))
    
    def clear_all_favorites(self):
        """清空所有收藏"""
        # 获取收藏数量
        if hasattr(self.main_app, 'get_favorites'):
            favorites = self.main_app.get_favorites()
            count = len(favorites)
        else:
            count = 0
            
        if count == 0:
            self.show_message("警告", "收藏列表已为空", "warning")
            return
        
        if self.show_message("确认", f"确定要清空所有收藏吗？共 {count} 首歌曲", "ask"):
            # 在主程序中清空收藏
            if hasattr(self.main_app, 'clear_all_favorites'):
                self.main_app.clear_all_favorites()
                self.refresh_favorites_display([])
                self.log("已清空所有收藏")
                self.show_message("成功", "已清空所有收藏", "info")