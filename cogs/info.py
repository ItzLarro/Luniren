import discord
import time
import asyncio
import pytz
from discord.ext import commands
from discord import Embed
from discord import app_commands
from discord import TextChannel
from discord.app_commands import Choice
from discord.abc import GuildChannel
from discord.enums import ChannelType
from discord.ext.commands import Greedy, Context
from typing import Dict, List, Optional, Tuple, Union, Literal
from datetime import datetime, timedelta, timezone
from humanize import precisedelta
from requests import get
from main import get_guild_prefixes, update_prefixes_in_database, default_prefixes

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.process_commands_start_time = {}

    @commands.hybrid_command()
    async def guildcount(self, ctx):
        """Displays the number of guilds the bot is in"""
        embed = discord.Embed(
            title="Guild Count",
            description=f"I am currently in **{len(self.bot.guilds)}** guilds!",
            color=discord.Color.blue(),
            timestamp=ctx.message.created_at
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def ping(self, ctx):
        """Check the bot's latency"""
        latency = round(self.bot.latency * 1000)
        start_time = time.time()
        await ctx.typing()
        measured_time = time.time() - start_time
        final = round(measured_time * 1000)
        if latency < 250:
            color = discord.Color.blue()
        elif latency < 450:
            color = discord.Color.green()
        elif latency < 600:
            color = discord.Color.orange()
        elif latency < 800:
            color = discord.Color.red()
        else:
            color = discord.Color.dark_red()
        embed = discord.Embed(title=f"Pong!", color=color, timestamp=ctx.message.created_at)
        embed.add_field(name="Websocket", value=f"```json\n{latency} ms```", inline=False)
        embed.add_field(name="Typing", value=f"```json\n{final} ms```", inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name='help')
    @app_commands.describe(command_name="Command to get help for.")
    async def help_command(self, ctx, *, command_name: str = None):
        """Displays a list of available commands or help for a specific command."""
        if command_name is None:
            embed = discord.Embed(
                title='Available Commands',
                description=f"Type `{ctx.clean_prefix}help` followed by a command name to see more details about that particular command.",
                color=discord.Color.blurple()
            )
            embed.add_field(
                name=":circus_tent: FUN COMMANDS",
                value="`roll`, `8ball`, `choose`, `rps`, `coinflip`, `compliment`, `dadjoke`",
                inline=False
            )
            embed.add_field(
                name="📸 IMAGE COMMANDS",
                value="`cat`, `dog`, `avatar`, `avatarserver`, `banner`, `bannerserver`",
                inline=False
            )
            embed.add_field(
                name=":hammer: MODERATION COMMANDS",
                value="`announce`, `ban`, `banlist`, `cleanup`, `createchannel`, `createrole`, `deleterole`, `deletechannel`, `dump`, `hackban`, `kick`, `listchannel`, `lock`, `lockdown`, `massban`, `massunban`, `mute`, `nickname`, `purge`, `perms`, `deletechannel`, `role`, `rolelist`, `slowmode`, `tempban`, `tempmute`, `temprole`, `unban`, `unlock`, `unlockdown`, `unmute`, `unviewlock`, `viewlock`, `warn`, `movechannel`, `rename`, `nukechannel`, `clone`, `topic`, `deafen`, `undeafen`, `softban`, `decancer`, `dehoist`",
                inline=False
            )
            embed.add_field(
                name="🛠️ UTILITY COMMANDS",
                value="`calculate`, `dm`, `left`, `rules`, `password`, `poll`, `say`, `id`, `time`, `userinfo`, `channelinfo`, `serverinfo`, `roleinfo`, `access`, `joined`, `firstmessage`, `importemoji`, `redirect`, `messages`, `randomcolor`, `membercount`, `quote`, `remind`, `snipe`, `editsnipe`, `afk`, `oldest`, `youngest`",
                inline=False
            )
            embed.add_field(
                name=":information_source: INFO COMMANDS",
                value="`guildcount`, `ping`, `help`, `prefix`, `status`, `version`, `uptime`, `sync`, `invite`, `contact`",
                inline=False
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.send(embed=embed)
        else:
            command = self.bot.get_command(command_name)
            if command is None:
                await ctx.send(f"Command '{command_name}' not found.", ephemeral=True)
                return
            command_help = command.help or "No help available."
            prefix = ctx.clean_prefix
            embed = discord.Embed(
                title=f"Help for {command_name}",
                description=command_help,
                color=discord.Color.blurple()
            )
            embed.add_field(
                name="Usage",
                value=f"`{prefix}{command.name} {command.signature}`",
                inline=False
            )
            if command.aliases:
                embed.add_field(
                    name="Aliases",
                    value=", ".join(f"`{alias}`" for alias in command.aliases),
                    inline=False
                )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @app_commands.choices(
        option=[
            app_commands.Choice(name="Add", value="add"),
            app_commands.Choice(name="Remove", value="remove"),
            app_commands.Choice(name="Clear", value="clear")
        ]
    )
    @app_commands.describe(
        option="Add, remove or clear prefixes",
        new_prefix="New prefix to use, example: !"
    )
    async def prefix(self, ctx, option: str = None, new_prefix: str = None):
        """Get or set command prefix for this server"""
        guild_id = str(ctx.guild.id)
        current_prefixes = get_guild_prefixes(guild_id)  # Imported or passed via bot
        if option is None:
            embed = discord.Embed(title="Prefixes", color=0x3EA6FF)
            embed.add_field(
                name="Current Prefixes",
                value="\n".join(f"{i+1}. `{p}`" for i, p in enumerate(current_prefixes)),
                inline=False
            )
            embed.set_footer(text=f"{len(current_prefixes)} prefixes | Requested by {ctx.author.display_name}")
            await ctx.send(embed=embed)
        elif option.lower() == "add":
            if not new_prefix:
                await ctx.send("Please provide a prefix to add.", ephemeral=True)
                return
            if new_prefix in current_prefixes:
                await ctx.send(f"The prefix `{new_prefix}` is already set for this server.", ephemeral=True)
                return
            current_prefixes.append(new_prefix)
            self.bot.prefixes[guild_id] = current_prefixes
            update_prefixes_in_database(guild_id, current_prefixes)  # Imported or passed via bot
            await ctx.send(f"Added prefix `{new_prefix}` for this server.")
        elif option.lower() == "remove":
            if not new_prefix:
                await ctx.send("Please provide a prefix to remove.", ephemeral=True)
                return
            if new_prefix not in current_prefixes:
                await ctx.send(f"The prefix `{new_prefix}` is not set for this server.", ephemeral=True)
                return
            current_prefixes.remove(new_prefix)
            self.bot.prefixes[guild_id] = current_prefixes
            update_prefixes_in_database(guild_id, current_prefixes)
            await ctx.send(f"Removed prefix `{new_prefix}` from this server.")
        elif option.lower() == "clear":
            self.bot.prefixes[guild_id] = default_prefixes
            update_prefixes_in_database(guild_id, default_prefixes)
            await ctx.send("All prefixes cleared. Set to default prefixes.")
        else:
            # If option is provided but doesn't match add/remove/clear, treat it as a new prefix
            if option:
                self.bot.prefixes[guild_id] = [option]
                update_prefixes_in_database(guild_id, [option])
                await ctx.send(f"Set prefix for this server to `{option}`.")
            else:
                await ctx.send("Invalid option. Use `add`, `remove`, `clear`, or specify a new prefix.", ephemeral=True)
    
    # status command
    @commands.hybrid_command()
    @commands.is_owner()

    @app_commands.choices(
        activity=[
            Choice(name="Playing", value="playing"),
            Choice(name="Streaming", value="streaming"),
            Choice(name="Listening", value="listening"),
            Choice(name="Watching", value="watching"),
            Choice(name="Competing", value="competing")
        ],
        status=[
            Choice(name="Online", value="online"),
            Choice(name="Idle", value="idle"),
            Choice(name="Do Not Disturb", value="dnd"),
            Choice(name="Invisible", value="invisible")
        ]
    )
    @app_commands.describe(
        activity="Activity for the bot.",
        status="Bot's discord status.",
        url="Link for stream. Example: https://twitch.tv/luniren",
        message="Custom status message."
    )
    async def status(self, ctx, activity, status, url=None, message=None):
        """Sets bot status"""

        if activity.lower() == 'playing':
            activity_type = discord.ActivityType.playing
        elif activity.lower() == 'streaming':
            activity_type = discord.ActivityType.streaming
        elif activity.lower() == 'listening':
            activity_type = discord.ActivityType.listening
        elif activity.lower() == 'watching':
            activity_type = discord.ActivityType.watching
        elif activity.lower() == 'competing':
            activity_type = discord.ActivityType.competing    
        else:
            await ctx.send(f'Invalid activity type: {activity}', ephemeral=True)
            return


        if status.lower() == 'online':
            status_type = discord.Status.online
        elif status.lower() == 'idle':
            status_type = discord.Status.idle
        elif status.lower() == 'dnd':
            status_type = discord.Status.dnd
        elif status.lower() == 'invisible':
            status_type = discord.Status.invisible
        else:
            await ctx.send(f'Invalid status type: {status}', ephemeral=True)
            return

        
        activity_name = activity if message is None else message

        if activity_name:
            if 'servercount' in activity_name:
                guild_count = len(self.bot.guilds)
                activity_name = activity_name.replace('servercount', str(guild_count))
            if 'usercount' in activity_name:
                user_count = sum(guild.member_count for guild in self.bot.guilds)
                activity_name = activity_name.replace('usercount', str(user_count))


        if url is not None:
            activity = discord.Activity(type=activity_type, name=f"{activity_name}", url=url)
        else:
            activity = discord.Activity(type=activity_type, name=f"{activity_name}")
        
        await self.bot.change_presence(activity=activity, status=status_type) 
    
        await ctx.send(f'Successfully changed bot status to {activity_name} {status}')
    
    @commands.hybrid_command()
    async def uptime(self, ctx):
        """Checks bot uptime"""
        delta_uptime = datetime.now(pytz.UTC) - self.bot.start_time
        days = delta_uptime.days
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        hours = hours % 24
        minutes, seconds = divmod(remainder, 60)
        unix_timestamp_uptime = int(self.bot.start_time.timestamp())
        uptime = f"<t:{unix_timestamp_uptime}:f>"
        embed = discord.Embed(title="Uptime", description=f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds (since {uptime})", color=discord.Color.green())
        await ctx.send(embed=embed)




    @commands.hybrid_command()
    async def invite(self, ctx):
        """Provides an invite link for the bot"""
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=discord.Permissions(administrator=True),
            scopes=("bot", "applications.commands")
        )
        embed = discord.Embed(
            title="Invite Me!",
            description=f"Click [here]({invite_url}) to invite me to your server!",
            color=discord.Color.blue(),
            timestamp=ctx.message.created_at
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command()
    async def contact(self, ctx):
        """Provides contact information for the bot's owner"""
        embed = discord.Embed(
            title="Contact Information",
            description="For support or inquiries, reach out to my creator!",
            color=discord.Color.blue(),
            timestamp=ctx.message.created_at
        )
        embed.add_field(
            name="Owner",
            value="<@753698418752487426>",  
            inline=False
        )
        embed.add_field(
            name="Support Server",
            value="[Join here](https://discord.gg/your-support-server)",  # Replace with actual link
            inline=False
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)



    @commands.hybrid_command()
    async def version(self, ctx):
        """Checks which version of Luniren this instance is running."""
        await ctx.send(f"This instance is running version `{self.bot.version}`.")

    @commands.hybrid_command()
    @commands.is_owner()
    @app_commands.describe(version="Set bot version.")
    async def setversion(self, ctx, version):
        """Sets the version of Luniren for the current instance"""
        self.bot.version = version

        await ctx.send(f"This instance has been set to version `{version}`.")








async def setup(bot):
    await bot.add_cog(Info(bot))

