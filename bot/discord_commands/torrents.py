import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup, Option
from config import settings
from services.qbittorrent_client import qbt_client
import aiohttp

class Torrents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    torrent = SlashCommandGroup("torrent", "Torrent management", guild_ids=[settings.DISCORD_GUILD_ID])

    def is_authorized(self, ctx):
        return ctx.author.id in settings.DISCORD_ADMIN_USER_IDS

    @torrent.command(name="add_link", description="Add a torrent from a URL")
    async def add_link(
        self,
        ctx,
        url: Option(str, "Magnet link or HTTP/HTTPS URL"),
        category: Option(str, "Category", required=False, default=None),
        save_path: Option(str, "Save path", required=False, default=None)
    ):
        if not self.is_authorized(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        try:
            result = qbt_client.add_link(url, category, save_path)
            if result == "Ok.":
                await ctx.respond("Ok", ephemeral=True)
            else:
                await ctx.respond(f"Result: {result}", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"Error: {str(e)}", ephemeral=True)

    @torrent.command(name="add_file", description="Add a torrent from a file")
    async def add_file(
        self,
        ctx,
        file: Option(discord.Attachment, "Torrent file"),
        category: Option(str, "Category", required=False, default=None),
        save_path: Option(str, "Save path", required=False, default=None)
    ):
        if not self.is_authorized(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        if not file.filename.endswith(".torrent"):
            await ctx.respond("Please upload a .torrent file.", ephemeral=True)
            return

        try:
            file_content = await file.read()
            result = qbt_client.add_file(file_content, category, save_path)
            if result == "Ok.":
                await ctx.respond("Ok", ephemeral=True)
            else:
                await ctx.respond(f"Result: {result}", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"Error: {str(e)}", ephemeral=True)

def setup(bot):
    bot.add_cog(Torrents(bot))
