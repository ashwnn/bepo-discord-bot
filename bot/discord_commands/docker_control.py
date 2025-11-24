import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup, Option
from discord.ui import View, Button
from config import settings
from services.docker_client import DockerClient
from services.confirmations import confirmation_manager
from services.server_manager import server_manager

class ConfirmationView(View):
    def __init__(self, token: str, action_type: str):
        super().__init__(timeout=120)
        self.token = token
        self.action_type = action_type

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger, custom_id="confirm_action")
    async def confirm_callback(self, button, interaction):
        # Verify ownership of the action
        action = confirmation_manager.consume(self.token)
        if not action:
            await interaction.response.edit_message(content="Action expired or already used.", view=None)
            return

        if interaction.user.id != action["user_id"]:
             await interaction.response.send_message("You cannot confirm this action.", ephemeral=True)
             return

        await interaction.response.defer() # Acknowledge interaction

        # Execute action based on type
        server_name = action.get("server_name")
        server = server_manager.get_server(server_name)
        
        if not server:
            await interaction.edit_original_response(content=f"Server '{server_name}' not found.", view=None)
            return
        
        docker_client = DockerClient(server)

        if self.action_type == "docker_pause_all":
            count = docker_client.pause_all()
            await interaction.edit_original_response(content=f"Success: Paused {count} containers on {server.display_name}.", view=None)
        elif self.action_type == "docker_resume_all":
            count = docker_client.resume_all()
            await interaction.edit_original_response(content=f"Success: Resumed {count} containers on {server.display_name}.", view=None)
        else:
             await interaction.edit_original_response(content="Unknown action.", view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel_action")
    async def cancel_callback(self, button, interaction):
        confirmation_manager.consume(self.token) # Consume to invalidate
        await interaction.response.edit_message(content="Action cancelled.", view=None)


class DockerControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    docker = SlashCommandGroup("docker", "Docker container management", guild_ids=[settings.DISCORD_GUILD_ID])

    def is_admin(self, ctx):
        return ctx.author.id in settings.DISCORD_ADMIN_USER_IDS

    async def get_server_names(self, ctx: discord.AutocompleteContext):
        """Autocomplete for servers with Docker feature"""
        servers = server_manager.get_servers_with_feature("docker")
        server_names = [s.name for s in servers]
        return [name for name in server_names if name.lower().startswith(ctx.value.lower())]

    async def get_container_names(self, ctx: discord.AutocompleteContext):
        """Autocomplete for container names from selected server"""
        # Get the server from the current options
        server_name = ctx.options.get("server")
        if not server_name:
            return []
        
        server = server_manager.get_server(server_name)
        if not server:
            return []
        
        try:
            docker_client = DockerClient(server)
            containers = docker_client.list_containers()
            return [c for c in containers if c.lower().startswith(ctx.value.lower())]
        except:
            return []

    @docker.command(description="Pause all Docker containers")
    async def pause_all(
        self,
        ctx,
        server: Option(str, "Server name", autocomplete=get_server_names)
    ):
        if not self.is_admin(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        # Validate server and feature
        is_valid, error_msg = server_manager.validate_server_feature(server, "docker")
        if not is_valid:
            await ctx.respond(error_msg, ephemeral=True)
            return

        server_config = server_manager.get_server(server)
        token = confirmation_manager.create(ctx.author.id, "docker_pause_all", server_name=server)
        view = ConfirmationView(token, "docker_pause_all")
        await ctx.respond(
            f"This will pause all running Docker containers on **{server_config.display_name}**. Confirm?",
            view=view,
            ephemeral=True
        )

    @docker.command(description="Resume all Docker containers")
    async def resume_all(
        self,
        ctx,
        server: Option(str, "Server name", autocomplete=get_server_names)
    ):
        if not self.is_admin(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        # Validate server and feature
        is_valid, error_msg = server_manager.validate_server_feature(server, "docker")
        if not is_valid:
            await ctx.respond(error_msg, ephemeral=True)
            return

        server_config = server_manager.get_server(server)
        token = confirmation_manager.create(ctx.author.id, "docker_resume_all", server_name=server)
        view = ConfirmationView(token, "docker_resume_all")
        await ctx.respond(
            f"This will resume all paused Docker containers on **{server_config.display_name}**. Confirm?",
            view=view,
            ephemeral=True
        )

    @docker.command(description="Restart a specific container")
    async def restart(
        self,
        ctx,
        server: Option(str, "Server name", autocomplete=get_server_names),
        container: Option(str, "Container name", autocomplete=get_container_names)
    ):
        if not self.is_admin(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return
        
        # Validate server and feature
        is_valid, error_msg = server_manager.validate_server_feature(server, "docker")
        if not is_valid:
            await ctx.respond(error_msg, ephemeral=True)
            return
        
        await ctx.defer(ephemeral=True)
        
        server_config = server_manager.get_server(server)
        docker_client = DockerClient(server_config)
        result = docker_client.restart_container(container)
        await ctx.respond(result, ephemeral=True)

    @docker.command(description="Get logs for a container")
    async def logs(
        self,
        ctx,
        server: Option(str, "Server name", autocomplete=get_server_names),
        container: Option(str, "Container name", autocomplete=get_container_names),
        tail: Option(int, "Number of lines", default=20, required=False)
    ):
        if not self.is_admin(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return
        
        # Validate server and feature
        is_valid, error_msg = server_manager.validate_server_feature(server, "docker")
        if not is_valid:
            await ctx.respond(error_msg, ephemeral=True)
            return
        
        await ctx.defer(ephemeral=True)
        
        server_config = server_manager.get_server(server)
        docker_client = DockerClient(server_config)
        logs = docker_client.get_container_logs(container, tail)
        
        if len(logs) > 1900:
            logs = logs[-1900:] + "\n... (truncated)"
        
        if not logs.strip():
            logs = "No logs found or empty."

        await ctx.respond(f"**Logs for {container} on {server_config.display_name}**\n```\n{logs}\n```", ephemeral=True)

def setup(bot):
    bot.add_cog(DockerControl(bot))

