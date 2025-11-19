import docker
from config import settings

class DockerClient:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            print(f"Failed to initialize Docker client: {e}")
            self.client = None

    def pause_all(self):
        if not self.client:
            return "Docker client not initialized."
        
        paused_count = 0
        for container in self.client.containers.list():
            if container.status == "running":
                # Don't pause ourselves!
                # We can check container name or ID, but name is easier if we know it.
                # In docker-compose we set container_name: discord-server-bot
                if container.name == "discord-server-bot":
                    continue
                
                try:
                    container.pause()
                    paused_count += 1
                except Exception as e:
                    print(f"Failed to pause {container.name}: {e}")
        return paused_count

    def resume_all(self):
        if not self.client:
            return "Docker client not initialized."

        resumed_count = 0
        for container in self.client.containers.list(all=True):
            if container.status == "paused":
                try:
                    container.unpause()
                    resumed_count += 1
                except Exception as e:
                    print(f"Failed to unpause {container.name}: {e}")
        return resumed_count

    def list_containers(self):
        if not self.client:
            return []
        try:
            return [c.name for c in self.client.containers.list(all=True)]
        except Exception as e:
            print(f"Failed to list containers: {e}")
            return []

    def restart_container(self, container_name: str):
        if not self.client:
            return "Docker client not initialized."
        try:
            container = self.client.containers.get(container_name)
            container.restart()
            return f"Successfully restarted {container_name}"
        except docker.errors.NotFound:
            return f"Container {container_name} not found."
        except Exception as e:
            return f"Failed to restart {container_name}: {e}"

    def get_container_logs(self, container_name: str, tail: int = 20):
        if not self.client:
            return "Docker client not initialized."
        try:
            container = self.client.containers.get(container_name)
            # logs returns bytes, need to decode
            logs = container.logs(tail=tail).decode('utf-8')
            return logs
        except docker.errors.NotFound:
            return f"Container {container_name} not found."
        except Exception as e:
            return f"Failed to get logs for {container_name}: {e}"

docker_service = DockerClient()
