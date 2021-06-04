from discord.ext import commands
import json
import time

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

CACHE_PATH = Path(".cache")

gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

bot = commands.Bot(command_prefix="!")

@bot.command(name="download", help="Downloads selected attachment.")
async def download(ctx, id):
    message = await ctx.channel.fetch_message(id)
    await ctx.send(message.attachments[0].filename)
    await message.attachments[0].save(f"save_files/{message.attachments[0].filename}")

@bot.command(name="update", help="Download all attachments in channel and uploads them to Drive")
async def update(ctx):
    # Load cache
    try:
        cache = load_cache(ctx.guild.id)
        messages = await ctx.channel.history(after = datetime.utcfromtimestamp(cache["time"])).flatten()
    except FileNotFoundError:
        cache = {}
        cache["time"] = time.time()
        messages = await ctx.channel.history().flatten()

    # Download every attachment
    for message in messages:
        if message.attachments:
            await message.attachments[0].save(f"save_files/{message.attachments[0].filename}")
            await ctx.channel.send(f"`Downloaded {message.attachments[0].filename}`")
            await upload(ctx, message.attachments[0].filename)

    cache["time"] = time.time()
    dump_cache(ctx.guild.id, cache)

@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))

async def upload(ctx, filename):
    file_path = "save_files/" + filename
    file_drive = drive.CreateFile({"title": os.path.basename(file_path)})
    file_drive.SetContentFile(file_path)
    file_drive.Upload()
    await ctx.send("File uploaded!")
    os.remove(file_path)

def load_cache(guild_id):
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)
    with open(CACHE_PATH/f"{guild_id}.json", "r") as f:
        return json.load(f)

def dump_cache(guild_id, cache):
    with open(CACHE_PATH/f"{guild_id}.json", "w") as f:
        json.dump(cache, f)

if __name__ == "__main__":
    bot.run(TOKEN)
