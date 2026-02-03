import discord
import asyncio
import json
import os
import pytz
from discord.ext import commands
from datetime import datetime
from discord.ext.commands import Greedy, Context
from typing import Dict, List, Optional, Tuple, Union, Literal
from humanize import precisedelta
from requests import get
from dotenv import load_dotenv


DB_PATH = 'database/prefixes.db'


default_prefixes = ["-", "larro", "l!", "luni"]

# verify
def ensure_prefixes_file():
    if not os.path.exists(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with open(DB_PATH, 'w') as db_file:
            json.dump({}, db_file)
    else:
        with open(DB_PATH, 'r+') as db_file:
            try:
                json.load(db_file)
            except json.JSONDecodeError:
                db_file.seek(0)
                db_file.truncate()
                json.dump({}, db_file)


def load_prefixes():
    ensure_prefixes_file()
    with open(DB_PATH, 'r') as db_file:
        return json.load(db_file)


def save_prefixes(prefixes):
    with open(DB_PATH, 'w') as db_file:
        json.dump(prefixes, db_file)


def get_guild_prefixes(guild_id):
    prefixes = load_prefixes()
    return prefixes.get(guild_id, default_prefixes)


def update_prefixes_in_database(guild_id, prefixes):
    data = load_prefixes()
    data[guild_id] = prefixes
    save_prefixes(data)


def get_prefix(bot, message):
    if message.guild:
        guild_id = str(message.guild.id)
        prefixes = get_guild_prefixes(guild_id)
    else:
        prefixes = default_prefixes
    return commands.when_mentioned_or(*prefixes)(bot, message)


intents = discord.Intents.all()
bot = commands.AutoShardedBot(
    command_prefix=get_prefix,
    intents=intents,
    activity=discord.Activity(type=discord.ActivityType.listening, name="Guilds"),
    status=discord.Status.idle,
    help_command=None,
    owner_ids=[753698418752487426, 810552352901562378],
    strip_after_prefix=True
)

bot.author_id = 753698418752487426
bot.start_time = datetime.now(pytz.UTC)
bot.prefixes = {}
bot.default_prefixes = default_prefixes
bot.get_guild_prefixes = get_guild_prefixes
bot.update_prefixes_in_database = update_prefixes_in_database
bot.version = "5.1.6a"


@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(ctx: Context, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")



async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
 
            await bot.load_extension(f'cogs.{filename[:-3]}')


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await load_cogs()





load_dotenv()


if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    bot.run(token, reconnect=True)