import qbittorrentapi
from config import ServerConfig


class QBittorrentClient:
    """Client for managing qBittorrent on remote servers"""
    
    def __init__(self, server: ServerConfig):
        """
        Initialize qBittorrent client for a specific server
        
        Args:
            server: Server configuration
        """
        self.server = server
        qb_config = server.get_qbittorrent_config()
        
        if not qb_config:
            raise ValueError(f"Server {server.name} does not have qBittorrent configuration")
        
        self.client = qbittorrentapi.Client(
            host=qb_config['base_url'],
            username=qb_config['username'],
            password=qb_config['password'],
        )
        
        try:
            self.client.auth_log_in()
        except qbittorrentapi.LoginFailed as e:
            print(f"Failed to login to qBittorrent on {server.display_name}: {e}")
    
    def add_link(self, url: str, category: str = None, save_path: str = None):
        """
        Add a torrent via magnet link or URL
        
        Args:
            url: Magnet link or torrent URL
            category: Optional category
            save_path: Optional save path
            
        Returns:
            Result of the add operation
        """
        kwargs = {}
        if category:
            kwargs['category'] = category
        if save_path:
            kwargs['save_path'] = save_path
        
        return self.client.torrents_add(urls=url, **kwargs)
    
    def add_file(self, file_content: bytes, category: str = None, save_path: str = None):
        """
        Add a torrent via .torrent file
        
        Args:
            file_content: Torrent file content as bytes
            category: Optional category
            save_path: Optional save path
            
        Returns:
            Result of the add operation
        """
        kwargs = {}
        if category:
            kwargs['category'] = category
        if save_path:
            kwargs['save_path'] = save_path
        
        return self.client.torrents_add(torrent_files=file_content, **kwargs)

