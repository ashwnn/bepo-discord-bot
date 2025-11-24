from config import ServerConfig
from services.ssh_executor import ssh_executor


def get_disk_usage(server: ServerConfig, path_key: str) -> str:
    """
    Get disk usage for a specific path on a remote server
    
    Args:
        server: Server configuration
        path_key: Key identifying the path in server config
        
    Returns:
        Disk usage string in human-readable format
    """
    fs_config = server.get_filesystem_config()
    if not fs_config:
        return f"Server {server.name} does not have filesystem configuration"
    
    paths = fs_config.get('paths', {})
    path = paths.get(path_key)
    
    if not path:
        available_paths = ', '.join(paths.keys()) if paths else 'none'
        return f"Invalid path key '{path_key}'. Available paths: {available_paths}"
    
    # Execute du command remotely
    cmd = f"du -sh {path}"
    stdout, stderr, exit_code = ssh_executor.execute_command(server, cmd, timeout=30)
    
    if exit_code == 0:
        return stdout.strip()
    else:
        return f"Error checking disk usage: {stderr}"


def get_available_paths(server: ServerConfig) -> list[str]:
    """
    Get list of available filesystem paths for a server
    
    Args:
        server: Server configuration
        
    Returns:
        List of path keys
    """
    fs_config = server.get_filesystem_config()
    if not fs_config:
        return []
    
    return list(fs_config.get('paths', {}).keys())

