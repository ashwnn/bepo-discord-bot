import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup, Option
from discord.ui import View, Button
from config import settings
from services.snapraid_runner import run_snapraid_command
from services.confirmations import confirmation_manager
from services.server_manager import server_manager
import asyncio

class SnapRAIDConfirmationView(View):
    def __init__(self, token: str, action_type: str):
        super().__init__(timeout=120)
        self.token = token
        self.action_type = action_type

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger, custom_id="confirm_snapraid")
    async def confirm_callback(self, button, interaction):
        action = confirmation_manager.consume(self.token)
        if not action:
            await interaction.response.edit_message(content="Action expired or already used.", view=None)
            return

        if interaction.user.id != action["user_id"]:
             await interaction.response.send_message("You cannot confirm this action.", ephemeral=True)
             return

        server_name = action.get("server_name")
        server = server_manager.get_server(server_name)
        
        if not server:
            await interaction.response.edit_message(content=f"Server '{server_name}' not found.", view=None)
            return

        await interaction.response.edit_message(
            content=f"{self.action_type} started on {server.display_name} in background...",
            view=None
        )
        
        loop = asyncio.get_running_loop()
        
        try:
            result = await loop.run_in_executor(None, run_snapraid_command, server, self.action_type)
            if len(result) > 1900:
                result = result[:1900] + "\n... (truncated)"
            
            await interaction.followup.send(
                f"**SnapRAID {self.action_type} Finished on {server.display_name}**\n```\n{result}\n```",
                ephemeral=True
            )
        except Exception as e:
             await interaction.followup.send(f"SnapRAID {self.action_type} failed: {e}", ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel_snapraid")
    async def cancel_callback(self, button, interaction):
        confirmation_manager.consume(self.token)
        await interaction.response.edit_message(content="Action cancelled.", view=None)

class SnapRAID(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    snapraid = SlashCommandGroup("snapraid", "SnapRAID management", guild_ids=[settings.DISCORD_GUILD_ID])

    def is_admin(self, ctx):
        return ctx.author.id in settings.DISCORD_ADMIN_USER_IDS

    async def get_server_names(self, ctx: discord.AutocompleteContext):
        """Autocomplete for servers with SnapRAID feature"""
        servers = server_manager.get_servers_with_feature("snapraid")
        server_names = [s.name for s in servers]
        return [name for name in server_names if name.lower().startswith(ctx.value.lower())]

    @snapraid.command(description="Get SnapRAID status")
    async def status(
        self,
        ctx,
        server: Option(str, "Server name", autocomplete=get_server_names)
    ):
        # Validate server and feature
        is_valid, error_msg = server_manager.validate_server_feature(server, "snapraid")
        if not is_valid:
            await ctx.respond(error_msg, ephemeral=True)
            return

        await ctx.defer(ephemeral=True)
        server_config = server_manager.get_server(server)
        result = await asyncio.to_thread(run_snapraid_command, server_config, "status")
        if len(result) > 1900:
            result = result[:1900] + "\n... (truncated)"
        await ctx.respond(f"**SnapRAID Status on {server_config.display_name}**\n```\n{result}\n```", ephemeral=True)

    @snapraid.command(description="Get SnapRAID SMART stats")
    async def smart(
        self,
        ctx,
        server: Option(str, "Server name", autocomplete=get_server_names)
    ):
        # Validate server and feature
        is_valid, error_msg = server_manager.validate_server_feature(server, "snapraid")
        if not is_valid:
            await ctx.respond(error_msg, ephemeral=True)
            return

        await ctx.defer(ephemeral=True)
        server_config = server_manager.get_server(server)
        result = await asyncio.to_thread(run_snapraid_command, server_config, "smart")
        if len(result) > 1900:
            result = result[:1900] + "\n... (truncated)"
        await ctx.respond(f"**SnapRAID SMART on {server_config.display_name}**\n```\n{result}\n```", ephemeral=True)

    async def _dangerous_command(self, ctx, server: str, command_name: str, warning: str):
        if not self.is_admin(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        # Validate server and feature
        is_valid, error_msg = server_manager.validate_server_feature(server, "snapraid")
        if not is_valid:
            await ctx.respond(error_msg, ephemeral=True)
            return

        server_config = server_manager.get_server(server)
        token = confirmation_manager.create(ctx.author.id, command_name, server_name=server)
        view = SnapRAIDConfirmationView(token, command_name)
        await ctx.respond(
            f"{warning} This will run on **{server_config.display_name}**. Confirm?",
            view=view,
            ephemeral=True
        )

    @snapraid.command(description="Run SnapRAID sync")
    async def sync(
        self,
        ctx,
        server: Option(str, "Server name", autocomplete=get_server_names)
    ):
        await self._dangerous_command(
            ctx,
            server,
            "sync",
            "SnapRAID sync may run for a long time and will rewrite parity."
        )

    @snapraid.command(description="Run SnapRAID scrub")
    async def scrub(
        self,
        ctx,
        server: Option(str, "Server name", autocomplete=get_server_names)
    ):
        await self._dangerous_command(
            ctx,
            server,
            "scrub",
            "SnapRAID scrub checks data integrity."
        )

    @snapraid.command(description="Run SnapRAID fix")
    async def fix(
        self,
        ctx,
        server: Option(str, "Server name", autocomplete=get_server_names)
    ):
        await self._dangerous_command(
            ctx,
            server,
            "fix",
            "SnapRAID fix will attempt to restore files. Ensure you know what you are doing!"
        )

def setup(bot):
    bot.add_cog(SnapRAID(bot))

