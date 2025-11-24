from config import ServerConfig
from services.ssh_executor import ssh_executor


def run_snapraid_command(server: ServerConfig, *args: str) -> str:
    """
    Run a SnapRAID command on a remote server
    
    Args:
        server: Server configuration
        *args: SnapRAID command arguments
        
    Returns:
        Command output
    """
    sr_config = server.get_snapraid_config()
    if not sr_config:
        return f"Server {server.name} does not have SnapRAID configuration"
    
    conf_path = sr_config['conf_path']
    cmd = f"snapraid -c {conf_path} {' '.join(args)}"
    
    # SnapRAID commands can take a while, especially sync/scrub
    timeout = 300  # 5 minutes
    stdout, stderr, exit_code = ssh_executor.execute_command(server, cmd, timeout)
    
    if exit_code == 0:
        return stdout.strip()
    else:
        return f"SnapRAID command failed:\n{stderr}"

