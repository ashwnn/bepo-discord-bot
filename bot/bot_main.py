import discord
from discord.ext import commands
from config import settings
import os

# Initialize bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

# Load extensions
extensions = [
    "discord_commands.torrents",
    "discord_commands.docker_control",
    "discord_commands.snapraid",
    "discord_commands.system",
]

if __name__ == "__main__":
    for extension in extensions:
        try:
            bot.load_extension(extension)
            print(f"Loaded extension: {extension}")
        except Exception as e:
            print(f"Failed to load extension {extension}: {e}")

    if settings.DISCORD_BOT_TOKEN:
        bot.run(settings.DISCORD_BOT_TOKEN)
    else:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables.")
