import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup, Option
from config import settings
from services.filesystem_stats import get_disk_usage, get_available_paths
from services.server_manager import server_manager
from services.ssh_executor import ssh_executor
import subprocess
import time

class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    system = SlashCommandGroup("system", "System information and utilities", guild_ids=[settings.DISCORD_GUILD_ID])

    async def get_server_names_filesystem(self, ctx: discord.AutocompleteContext):
        """Autocomplete for servers with filesystem feature"""
        servers = server_manager.get_servers_with_feature("filesystem")
        server_names = [s.name for s in servers]
        return [name for name in server_names if name.lower().startswith(ctx.value.lower())]

    async def get_server_names_all(self, ctx: discord.AutocompleteContext):
        """Autocomplete for all servers"""
        server_names = server_manager.get_server_names()
        return [name for name in server_names if name.lower().startswith(ctx.value.lower())]

    async def get_path_choices(self, ctx: discord.AutocompleteContext):
        """Autocomplete for filesystem paths based on selected server"""
        server_name = ctx.options.get("server")
        if not server_name:
            return []
        
        server = server_manager.get_server(server_name)
        if not server:
            return []
        
        paths = get_available_paths(server)
        return [p for p in paths if p.lower().startswith(ctx.value.lower())]

    @system.command(description="Check filesystem size")
    async def disk_usage(
        self,
        ctx,
        server: Option(str, "Server name", autocomplete=get_server_names_filesystem),
        path: Option(str, "Path to check", autocomplete=get_path_choices)
    ):
        # Validate server and feature
        is_valid, error_msg = server_manager.validate_server_feature(server, "filesystem")
        if not is_valid:
            await ctx.respond(error_msg, ephemeral=True)
            return

        server_config = server_manager.get_server(server)
        size_str = get_disk_usage(server_config, path)
        
        # Get the actual path for display
        fs_config = server_config.get_filesystem_config()
        actual_path = fs_config.get('paths', {}).get(path, path) if fs_config else path
        
        await ctx.respond(
            f"**Disk Usage on {server_config.display_name}**\nPath: `{actual_path}`\nSize: {size_str}",
            ephemeral=True
        )

    @system.command(description="Get system info (Uptime, IP)")
    async def info(
        self,
        ctx,
        server: Option(str, "Server name", autocomplete=get_server_names_all)
    ):
        # Validate server exists
        server_config = server_manager.get_server(server)
        if not server_config:
            await ctx.respond(f"Server '{server}' not found.", ephemeral=True)
            return

        await ctx.defer(ephemeral=True)
        
        # Uptime
        uptime_output, _, uptime_exit = ssh_executor.execute_command(server_config, "uptime -p", timeout=5)
        if uptime_exit != 0:
            uptime_output = "Error getting uptime"
        else:
            uptime_output = uptime_output.strip()

        # Public IP
        public_ip, _, ip_exit = ssh_executor.execute_command(server_config, "curl -s ifconfig.me", timeout=10)
        if ip_exit != 0:
            public_ip = "Error getting public IP"
        else:
            public_ip = public_ip.strip()

        # Bot Latency
        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(title=f"System Info - {server_config.display_name}", color=discord.Color.blue())
        embed.add_field(name="Uptime", value=uptime_output, inline=False)
        embed.add_field(name="Public IP", value=public_ip, inline=False)
        embed.add_field(name="Bot Latency", value=f"{latency}ms", inline=False)

        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(System(bot))

