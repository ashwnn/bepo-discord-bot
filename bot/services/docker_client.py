from typing import List
from config import ServerConfig
from services.ssh_executor import ssh_executor


class DockerClient:
    """Client for managing Docker containers on remote servers"""
    
    def __init__(self, server: ServerConfig):
        """
        Initialize Docker client for a specific server
        
        Args:
            server: Server configuration
        """
        self.server = server
        self.server_name = server.name
    
    def _execute_docker_command(self, command: str, timeout: int = 30) -> tuple[str, str, int]:
        """Execute a docker command on the remote server"""
        full_command = f"docker {command}"
        return ssh_executor.execute_command(self.server, full_command, timeout)
    
    def pause_all(self) -> int:
        """
        Pause all running Docker containers (except the bot itself)
        
        Returns:
            Number of containers paused
        """
        # Get list of running containers
        stdout, stderr, exit_code = self._execute_docker_command(
            "ps --format '{{.Names}}' --filter status=running"
        )
        
        if exit_code != 0:
            print(f"Failed to list containers: {stderr}")
            return 0
        
        container_names = [name.strip() for name in stdout.strip().split('\n') if name.strip()]
        paused_count = 0
        
        for container_name in container_names:
            # Don't pause the bot itself
            if container_name == "discord-server-bot":
                continue
            
            stdout, stderr, exit_code = self._execute_docker_command(f"pause {container_name}")
            if exit_code == 0:
                paused_count += 1
            else:
                print(f"Failed to pause {container_name}: {stderr}")
        
        return paused_count
    
    def resume_all(self) -> int:
        """
        Resume all paused Docker containers
        
        Returns:
            Number of containers resumed
        """
        # Get list of paused containers
        stdout, stderr, exit_code = self._execute_docker_command(
            "ps --format '{{.Names}}' --filter status=paused"
        )
        
        if exit_code != 0:
            print(f"Failed to list containers: {stderr}")
            return 0
        
        container_names = [name.strip() for name in stdout.strip().split('\n') if name.strip()]
        resumed_count = 0
        
        for container_name in container_names:
            stdout, stderr, exit_code = self._execute_docker_command(f"unpause {container_name}")
            if exit_code == 0:
                resumed_count += 1
            else:
                print(f"Failed to unpause {container_name}: {stderr}")
        
        return resumed_count
    
    def list_containers(self) -> List[str]:
        """
        List all Docker containers
        
        Returns:
            List of container names
        """
        stdout, stderr, exit_code = self._execute_docker_command(
            "ps -a --format '{{.Names}}'"
        )
        
        if exit_code != 0:
            print(f"Failed to list containers: {stderr}")
            return []
        
        container_names = [name.strip() for name in stdout.strip().split('\n') if name.strip()]
        return container_names
    
    def restart_container(self, container_name: str) -> str:
        """
        Restart a specific container
        
        Args:
            container_name: Name of the container to restart
            
        Returns:
            Status message
        """
        stdout, stderr, exit_code = self._execute_docker_command(f"restart {container_name}")
        
        if exit_code == 0:
            return f"Successfully restarted {container_name}"
        else:
            if "No such container" in stderr:
                return f"Container {container_name} not found."
            return f"Failed to restart {container_name}: {stderr}"
    
    def get_container_logs(self, container_name: str, tail: int = 20) -> str:
        """
        Get logs for a specific container
        
        Args:
            container_name: Name of the container
            tail: Number of lines to retrieve
            
        Returns:
            Container logs
        """
        stdout, stderr, exit_code = self._execute_docker_command(
            f"logs --tail {tail} {container_name}"
        )
        
        if exit_code == 0:
            return stdout
        else:
            if "No such container" in stderr:
                return f"Container {container_name} not found."
            return f"Failed to get logs for {container_name}: {stderr}"

