import os
import json
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ConnectionConfig:
    """SSH connection configuration for a server"""
    host: str
    port: int
    user: str
    key_path: str


@dataclass
class ServerConfig:
    """Configuration for a managed server"""
    name: str
    display_name: str
    connection: ConnectionConfig
    features: List[str]
    config: Dict[str, Any]
    
    def has_feature(self, feature: str) -> bool:
        """Check if this server supports a specific feature"""
        return feature in self.features
    
    def get_qbittorrent_config(self) -> Optional[Dict[str, str]]:
        """Get qBittorrent configuration if available"""
        return self.config.get("qbittorrent")
    
    def get_snapraid_config(self) -> Optional[Dict[str, str]]:
        """Get SnapRAID configuration if available"""
        return self.config.get("snapraid")
    
    def get_filesystem_config(self) -> Optional[Dict[str, Any]]:
        """Get filesystem configuration if available"""
        return self.config.get("filesystem")


class Settings:
    """Application settings and server configurations"""
    
    # Discord settings from .env
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    DISCORD_APP_ID = os.getenv("DISCORD_APP_ID")
    DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")
    DISCORD_ADMIN_USER_IDS = {
        int(x) for x in os.getenv("DISCORD_ADMIN_USER_IDS", "").split(",") if x.strip()
    }
    
    # Misc
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Server configurations
    _servers: Dict[str, ServerConfig] = {}
    
    @classmethod
    def load_servers(cls, config_path: str = "servers.json") -> None:
        """Load server configurations from JSON file"""
        try:
            # Try multiple possible locations for servers.json
            possible_paths = [
                config_path,
                os.path.join(os.path.dirname(__file__), "..", config_path),
                os.path.join("/app", config_path)
            ]
            
            servers_data = None
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        servers_data = json.load(f)
                    print(f"Loaded server configuration from: {path}")
                    break
            
            if servers_data is None:
                print(f"Warning: servers.json not found in any of: {possible_paths}")
                print("No servers configured. Bot will run with empty server list.")
                return
            
            # Parse and validate server configurations
            for server_data in servers_data.get("servers", []):
                try:
                    connection = ConnectionConfig(**server_data["connection"])
                    server = ServerConfig(
                        name=server_data["name"],
                        display_name=server_data["display_name"],
                        connection=connection,
                        features=server_data.get("features", []),
                        config=server_data.get("config", {})
                    )
                    
                    # Validate server configuration
                    cls._validate_server_config(server)
                    cls._servers[server.name] = server
                    print(f"Loaded server: {server.name} ({server.display_name}) with features: {', '.join(server.features)}")
                    
                except Exception as e:
                    print(f"Error loading server {server_data.get('name', 'unknown')}: {e}")
                    
        except FileNotFoundError:
            print(f"Warning: {config_path} not found. No servers configured.")
        except json.JSONDecodeError as e:
            print(f"Error parsing {config_path}: {e}")
        except Exception as e:
            print(f"Unexpected error loading servers: {e}")
    
    @classmethod
    def _validate_server_config(cls, server: ServerConfig) -> None:
        """Validate that server has required config for its enabled features"""
        if "qbittorrent" in server.features:
            qb_config = server.get_qbittorrent_config()
            if not qb_config or not all(k in qb_config for k in ["base_url", "username", "password"]):
                raise ValueError(f"Server {server.name} has qbittorrent feature but missing required config")
        
        if "snapraid" in server.features:
            sr_config = server.get_snapraid_config()
            if not sr_config or "conf_path" not in sr_config:
                raise ValueError(f"Server {server.name} has snapraid feature but missing conf_path")
        
        if "filesystem" in server.features:
            fs_config = server.get_filesystem_config()
            if not fs_config or "paths" not in fs_config:
                raise ValueError(f"Server {server.name} has filesystem feature but missing paths config")
    
    @classmethod
    def get_server(cls, name: str) -> Optional[ServerConfig]:
        """Get server configuration by name"""
        return cls._servers.get(name)
    
    @classmethod
    def get_all_servers(cls) -> List[ServerConfig]:
        """Get all configured servers"""
        return list(cls._servers.values())
    
    @classmethod
    def get_servers_with_feature(cls, feature: str) -> List[ServerConfig]:
        """Get all servers that support a specific feature"""
        return [s for s in cls._servers.values() if s.has_feature(feature)]
    
    @classmethod
    def get_server_names(cls) -> List[str]:
        """Get list of all server names"""
        return list(cls._servers.keys())


# Initialize settings singleton
settings = Settings()

# Load server configurations on module import
settings.load_servers()
