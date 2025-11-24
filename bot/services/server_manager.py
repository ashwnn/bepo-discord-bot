from typing import List, Optional
from config import settings, ServerConfig


class ServerManager:
    """Central service for server management and feature detection"""
    
    def get_server(self, name: str) -> Optional[ServerConfig]:
        """
        Get server configuration by name
        
        Args:
            name: Server name
            
        Returns:
            ServerConfig if found, None otherwise
        """
        return settings.get_server(name)
    
    def get_all_servers(self) -> List[ServerConfig]:
        """
        Get all configured servers
        
        Returns:
            List of all ServerConfig objects
        """
        return settings.get_all_servers()
    
    def get_servers_with_feature(self, feature: str) -> List[ServerConfig]:
        """
        Get all servers that support a specific feature
        
        Args:
            feature: Feature name (e.g., 'docker', 'snapraid', 'qbittorrent')
            
        Returns:
            List of ServerConfig objects that support the feature
        """
        return settings.get_servers_with_feature(feature)
    
    def has_feature(self, server_name: str, feature: str) -> bool:
        """
        Check if a server supports a specific feature
        
        Args:
            server_name: Name of the server
            feature: Feature name
            
        Returns:
            True if server supports the feature, False otherwise
        """
        server = self.get_server(server_name)
        if not server:
            return False
        return server.has_feature(feature)
    
    def get_server_names(self) -> List[str]:
        """
        Get list of all server names
        
        Returns:
            List of server names
        """
        return settings.get_server_names()
    
    def get_server_names_with_feature(self, feature: str) -> List[str]:
        """
        Get list of server names that support a specific feature
        
        Args:
            feature: Feature name
            
        Returns:
            List of server names
        """
        return [s.name for s in self.get_servers_with_feature(feature)]
    
    def validate_server_feature(self, server_name: str, feature: str) -> tuple[bool, str]:
        """
        Validate that a server exists and supports a feature
        
        Args:
            server_name: Name of the server
            feature: Required feature
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        server = self.get_server(server_name)
        
        if not server:
            return False, f"Server '{server_name}' not found. Available servers: {', '.join(self.get_server_names())}"
        
        if not server.has_feature(feature):
            available_features = ', '.join(server.features) if server.features else 'none'
            return False, f"Server '{server.display_name}' does not support '{feature}'. Available features: {available_features}"
        
        return True, ""


# Global server manager instance
server_manager = ServerManager()
