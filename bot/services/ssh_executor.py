import paramiko
import io
from typing import Tuple, Optional
from config import ServerConfig
import time


class SSHExecutor:
    """Service for executing commands on remote servers via SSH"""
    
    def __init__(self):
        self._connections = {}  # Connection pool
    
    def _get_connection(self, server: ServerConfig) -> paramiko.SSHClient:
        """Get or create SSH connection for a server"""
        key = server.name
        
        # Check if we have an existing connection
        if key in self._connections:
            client = self._connections[key]
            try:
                # Test if connection is still alive
                client.exec_command("echo test", timeout=2)
                return client
            except:
                # Connection is dead, remove it
                try:
                    client.close()
                except:
                    pass
                del self._connections[key]
        
        # Create new connection
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Load private key
            if server.connection.key_path:
                key = paramiko.RSAKey.from_private_key_file(server.connection.key_path)
                client.connect(
                    hostname=server.connection.host,
                    port=server.connection.port,
                    username=server.connection.user,
                    pkey=key,
                    timeout=10
                )
            else:
                # Fallback to password auth (not recommended)
                client.connect(
                    hostname=server.connection.host,
                    port=server.connection.port,
                    username=server.connection.user,
                    timeout=10
                )
            
            self._connections[key] = client
            return client
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {server.display_name}: {e}")
    
    def execute_command(
        self, 
        server: ServerConfig, 
        command: str, 
        timeout: int = 30
    ) -> Tuple[str, str, int]:
        """
        Execute a command on a remote server
        
        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        try:
            client = self._get_connection(server)
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            
            # Wait for command to complete
            exit_code = stdout.channel.recv_exit_status()
            
            stdout_str = stdout.read().decode('utf-8', errors='replace')
            stderr_str = stderr.read().decode('utf-8', errors='replace')
            
            return stdout_str, stderr_str, exit_code
            
        except Exception as e:
            return "", str(e), -1
    
    def execute_python_script(
        self, 
        server: ServerConfig, 
        script: str,
        timeout: int = 30
    ) -> Tuple[str, str, int]:
        """
        Execute a Python script on a remote server
        
        Args:
            server: Server configuration
            script: Python code to execute
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        # Escape the script for shell execution
        escaped_script = script.replace("'", "'\\''")
        command = f"python3 -c '{escaped_script}'"
        return self.execute_command(server, command, timeout)
    
    def upload_file(
        self, 
        server: ServerConfig, 
        local_path: str, 
        remote_path: str
    ) -> bool:
        """
        Upload a file to a remote server
        
        Args:
            server: Server configuration
            local_path: Local file path
            remote_path: Remote destination path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_connection(server)
            sftp = client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            return True
        except Exception as e:
            print(f"Failed to upload file to {server.display_name}: {e}")
            return False
    
    def upload_file_content(
        self,
        server: ServerConfig,
        content: bytes,
        remote_path: str
    ) -> bool:
        """
        Upload file content (bytes) to a remote server
        
        Args:
            server: Server configuration
            content: File content as bytes
            remote_path: Remote destination path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_connection(server)
            sftp = client.open_sftp()
            
            # Write content to remote file
            with sftp.file(remote_path, 'wb') as remote_file:
                remote_file.write(content)
            
            sftp.close()
            return True
        except Exception as e:
            print(f"Failed to upload file content to {server.display_name}: {e}")
            return False
    
    def test_connection(self, server: ServerConfig) -> bool:
        """
        Test if we can connect to a server
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            stdout, stderr, exit_code = self.execute_command(server, "echo 'connection_test'", timeout=5)
            return exit_code == 0 and "connection_test" in stdout
        except:
            return False
    
    def close_all(self):
        """Close all SSH connections"""
        for client in self._connections.values():
            try:
                client.close()
            except:
                pass
        self._connections.clear()


# Global SSH executor instance
ssh_executor = SSHExecutor()
