import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup, Option
from config import settings
from services.filesystem_stats import get_disk_usage
import subprocess
import time

class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    system = SlashCommandGroup("system", "System information and utilities", guild_ids=[settings.DISCORD_GUILD_ID])

    @system.command(description="Check filesystem size")
    async def disk_usage(
        self,
        ctx,
        target: Option(str, "Target path", choices=["pool", "jellyfin_media", "qbittorrent_downloads"])
    ):
        size_str = get_disk_usage(target)
        
        path_map = {
            "pool": settings.HOST_POOL_PATH,
            "jellyfin_media": settings.HOST_MEDIA_SUBPATH,
            "qbittorrent_downloads": settings.HOST_DOWNLOADS_SUBPATH
        }
        friendly_path = path_map.get(target, target)
        
        await ctx.respond(f"Size of `{friendly_path}`: {size_str}", ephemeral=True)

    @system.command(description="Get system info (Uptime, IP)")
    async def info(self, ctx):
        await ctx.defer(ephemeral=True)
        
        # Uptime
        try:
            uptime_output = subprocess.check_output(["uptime", "-p"], text=True).strip()
        except Exception as e:
            uptime_output = f"Error: {e}"

        # Public IP
        try:
            # Using curl to fetch public IP. 
            # Note: This depends on external service availability.
            public_ip = subprocess.check_output(["curl", "-s", "ifconfig.me"], text=True).strip()
        except Exception as e:
            public_ip = f"Error: {e}"

        # Bot Latency
        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(title="System Info", color=discord.Color.blue())
        embed.add_field(name="Uptime", value=uptime_output, inline=False)
        embed.add_field(name="Public IP", value=public_ip, inline=False)
        embed.add_field(name="Bot Latency", value=f"{latency}ms", inline=False)

        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(System(bot))
