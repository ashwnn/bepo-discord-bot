import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup, Option
from discord.ui import View, Button
from config import settings
from services.docker_client import docker_service
from services.confirmations import confirmation_manager

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

        # Execute action
        if self.action_type == "docker_pause_all":
            count = docker_service.pause_all()
            await interaction.edit_original_response(content=f"Success: Paused {count} containers.", view=None)
        elif self.action_type == "docker_resume_all":
            count = docker_service.resume_all()
            await interaction.edit_original_response(content=f"Success: Resumed {count} containers.", view=None)
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

    async def get_container_names(self, ctx: discord.AutocompleteContext):
        containers = docker_service.list_containers()
        return [c for c in containers if c.lower().startswith(ctx.value.lower())]

    @docker.command(description="Pause all Docker containers")
    async def pause_all(self, ctx):
        if not self.is_admin(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        token = confirmation_manager.create(ctx.author.id, "docker_pause_all")
        view = ConfirmationView(token, "docker_pause_all")
        await ctx.respond("This will pause all running Docker containers on the host. Confirm?", view=view, ephemeral=True)

    @docker.command(description="Resume all Docker containers")
    async def resume_all(self, ctx):
        if not self.is_admin(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        token = confirmation_manager.create(ctx.author.id, "docker_resume_all")
        view = ConfirmationView(token, "docker_resume_all")
        await ctx.respond("This will resume all paused Docker containers on the host. Confirm?", view=view, ephemeral=True)

    @docker.command(description="Restart a specific container")
    async def restart(
        self, 
        ctx, 
        container: Option(str, "Container name", autocomplete=get_container_names)
    ):
        if not self.is_admin(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return
        
        await ctx.defer(ephemeral=True)
        result = docker_service.restart_container(container)
        await ctx.respond(result, ephemeral=True)

    @docker.command(description="Get logs for a container")
    async def logs(
        self, 
        ctx, 
        container: Option(str, "Container name", autocomplete=get_container_names),
        tail: Option(int, "Number of lines", default=20, required=False)
    ):
        if not self.is_admin(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return
        
        await ctx.defer(ephemeral=True)
        logs = docker_service.get_container_logs(container, tail)
        
        if len(logs) > 1900:
            logs = logs[-1900:] + "\n... (truncated)"
        
        if not logs.strip():
            logs = "No logs found or empty."

        await ctx.respond(f"**Logs for {container}**\n```\n{logs}\n```", ephemeral=True)

def setup(bot):
    bot.add_cog(DockerControl(bot))
