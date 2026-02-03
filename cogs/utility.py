import discord
import random
import string
import asyncio
import datetime
import pytz
import time
import re
import requests
import humanize
import PIL
import urllib.parse
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
from discord import Embed
from typing import Optional, Union, Literal
from main import get_guild_prefixes, update_prefixes_in_database, default_prefixes
from PIL import Image
from io import BytesIO
from humanize import precisedelta
from requests import get
from urllib.parse import urlparse
from dateutil.relativedelta import relativedelta







class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sniped_messages = {}  # {guild_id: [(message, deletion_time)]}
        self.edited_messages = {}  # {guild_id: [(before_message, after_message, edit_time)]}
        self.afk_users = {}  # {user_id: {"reason": str, "timestamp": datetime}}

    @commands.hybrid_command(aliases=['calc'])
    @app_commands.describe(expression="What to calculate (e.g, 2+2)")
    async def calculate(self, ctx, *, expression: str):
        """Calculates a mathematical expression"""
        start_time = time.monotonic()
        try:
            result = eval(expression, {"__builtins__": {}}, {"sin": __import__("math").sin, "cos": __import__("math").cos, "tan": __import__("math").tan, "sqrt": __import__("math").sqrt})
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
            return
        end_time = time.monotonic()
        time_taken = round((end_time - start_time) * 1000, 2)
        approx_result = round(result, 2)
        raw_result = repr(result)
        embed = discord.Embed(title=f"Input: `{expression}`", color=discord.Color.blue())
        embed.add_field(name="Output", value=f"```{approx_result}```", inline=False)
        embed.add_field(name="Raw", value=f"```{raw_result}```", inline=False)
        embed.set_footer(text=f"Calculated in {time_taken} ms")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(member="User to dm.", message="Message to deliver.")
    async def dm(self, ctx, member: discord.Member, *, message: str):
        """Sends a DM to a specified user"""
        try:
            embed = discord.Embed(description=message, color=discord.Color.blue())
            embed.set_footer(text=f"Sent by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await member.send(embed=embed)
            await ctx.send(f"Message sent to {member.mention}.", ephemeral=True)
        except discord.Forbidden:
            await ctx.send("I can't DM that user.", ephemeral=True)

    @commands.command()
    @commands.guild_only()
    async def left(self, ctx):
        """Says user has left the chat and purges the command message"""
        response = f"**{ctx.author.name}** has left the chat."
        await ctx.send(response)
        await ctx.message.delete()

    @commands.command()
    @commands.guild_only()
    async def rules(self, ctx):
        """Displays server rules"""
        embed = discord.Embed(title="Server Rules", color=discord.Color.dark_blue())
        embed.add_field(name="1. No spamming or trolling", value="Breaking this rule may result in a warning or a ban.", inline=False)
        embed.add_field(name="2. Be respectful of others", value="Do not use hate speech, and treat others how you would like to be treated.", inline=False)
        embed.add_field(name="3. Keep discussions on-topic", value="If a conversation is not related to the channel topic, take it to the appropriate channel or direct messages.", inline=False)
        embed.add_field(name="4. No NSFW content", value="Do not post or share any content that is not safe for work or that violates Discord's terms of service.", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=['pw'])
    @app_commands.describe(length="Password length from 4-32.")
    async def password(self, ctx, length: int = 16):
        """Generates a random password"""
        if length < 4 or length > 32:
            await ctx.send("Password length must be between 4 and 32 characters.", ephemeral=True)
            return
        letters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(letters) for _ in range(length))
        embed = discord.Embed(title="Password Generator", description=f"Your password is: ||{password}||", color=discord.Color.green())
        await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        message="The poll message.",
        choice1="Choice 1",
        choice2="Choice 2",
        choice3="Choice 3",
        choice4="Choice 4",
        choice5="Choice 5",
        choice6="Choice 6",
        choice7="Choice 7",
        choice8="Choice 8",
        choice9="Choice 9",
        choice10="Choice 10"
    )
    async def poll(self, ctx, message: str, choice1: str, choice2: str, choice3: str = None, choice4: str = None, choice5: str = None, 
                   choice6: str = None, choice7: str = None, choice8: str = None, choice9: str = None, choice10: str = None):
        """Start a poll"""
        choices = [choice1, choice2] + [c for c in [choice3, choice4, choice5, choice6, choice7, choice8, choice9, choice10] if c]
        if len(choices) < 2 or len(choices) > 10:
            await ctx.send("Please provide 2 to 10 options for the poll.", ephemeral=True)
            return
        emojis = [f"{i}\u20e3" for i in range(1, 10)] + ["\U0001F51F"] if len(choices) == 10 else [f"{i}\u20e3" for i in range(1, len(choices) + 1)]
        poll_message = f"**{message}**\n\n" + "\n\n".join(f"{emoji} {choice}" for emoji, choice in zip(emojis, choices))
        embed = discord.Embed(title="", description=poll_message, color=discord.Color.blue(), timestamp=ctx.message.created_at)
        embed.set_footer(text=f"Poll by {ctx.author}")
        poll_msg = await ctx.send(embed=embed)
        for emoji in emojis:
            await poll_msg.add_reaction(emoji)
        await ctx.send(embed=discord.Embed(title="", description="✅ Poll created", color=discord.Color.green()), ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @app_commands.describe(channel="Channel to echo to.", message="Message to say.")
    async def say(self, ctx, channel: Optional[discord.TextChannel], *, message: str):
        """Sends a message in the specified channel"""
        channel = channel or ctx.channel
        await channel.send(message)
        await ctx.send(f"Message sent to {channel.mention}" if channel != ctx.channel else "Message sent", ephemeral=True)

    @commands.hybrid_command(name='id')
    @commands.guild_only()
    @app_commands.describe(thing="What you want to get the id of.")
    async def id(self, ctx, thing: str):
        """Displays the ID of a user, channel, emoji, or role"""
        thing = thing.strip()
        if thing.startswith('<@&') and thing.endswith('>'):
            role_id = int(thing[3:-1])
            role = ctx.guild.get_role(role_id)
            if role:
                await ctx.send(f"The ID of the role is: `{role_id}`")
            else:
                await ctx.send("I couldn't find that role.", ephemeral=True)
        elif thing.startswith('<@') and thing.endswith('>'):
            user_id = int(thing[2:-1].replace('!', ''))
            user = ctx.guild.get_member(user_id) or await self.bot.fetch_user(user_id)
            if user:
                await ctx.send(f"The ID of the user is: `{user_id}`")
            else:
                await ctx.send("I couldn't find that user.", ephemeral=True)
        elif thing.startswith('<#') and thing.endswith('>'):
            channel_id = int(thing[2:-1])
            channel = ctx.guild.get_channel(channel_id)
            if channel:
                await ctx.send(f"The ID of the channel is: `{channel_id}`")
            else:
                await ctx.send("I couldn't find that channel.", ephemeral=True)
        elif thing.startswith('<:') and thing.endswith('>'):
            emoji_id = int(thing.split(':')[2].strip('>'))
            await ctx.send(f"The ID of the custom emoji is: `{emoji_id}`")
        else:
            await ctx.send("Please provide a valid mention (user, role, channel, or emoji).", ephemeral=True)

    @commands.hybrid_command()
    @app_commands.describe(timezone="Timezone to get time of.")
    async def time(self, ctx, timezone: str = 'GMT'):
        """Displays the current time in the specified timezone"""
        try:
            target_timezone = pytz.timezone(timezone.upper())
        except pytz.UnknownTimeZoneError:
            await ctx.send("Invalid timezone. Please provide a valid timezone name.", ephemeral=True)
            return
        current_time = datetime.datetime.now(pytz.utc).astimezone(target_timezone)
        unix_timestamp = int(current_time.timestamp())
        embed = discord.Embed(title="Current Time", description=f"<t:{unix_timestamp}:T>", color=discord.Color.blue())
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=['ui'])
    @commands.guild_only()
    @app_commands.describe(member="The user to get information about.")
    async def userinfo(self, ctx, *, member: discord.Member = None):
        """Displays information about a user"""
        member = member or ctx.author
        embed = discord.Embed(color=member.color, timestamp=ctx.message.created_at)
        embed.set_author(name=member.name, url=member.avatar.url, icon_url=member.avatar.url)
        embed.add_field(name="", value=f"[Avatar]({member.avatar.url})", inline=False)
        embed.add_field(name="Roles", value=" ".join(f"<@&{r.id}>" for r in member.roles[1:]) or "None", inline=True)
        embed.add_field(name="Created at", value=f"<t:{int(member.created_at.timestamp())}:F> (<t:{int(member.created_at.timestamp())}:R>)", inline=True)
        embed.add_field(name="Joined at", value=f"<t:{int(member.joined_at.timestamp())}:F> (<t:{int(member.joined_at.timestamp())}:R>)", inline=True)
        embed.add_field(name="", value=f"ID: {member.id}", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=['cinfo'])
    @commands.guild_only()
    @app_commands.describe(channel="The channel to get information about.")
    async def channelinfo(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Displays information about a channel"""
        channel = channel or ctx.channel
        embed = discord.Embed(title="Channel Info", color=discord.Color.dark_purple(), timestamp=ctx.message.created_at)
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.add_field(name="Name", value=f"{channel.name}", inline=False)
        embed.add_field(name="ID", value=channel.id, inline=True)
        embed.add_field(name="Type", value=f"{channel.type} channel", inline=True)
        embed.add_field(name="Created", value=f"<t:{int(channel.created_at.timestamp())}:F> (<t:{int(channel.created_at.timestamp())}:R>)", inline=False)
        embed.add_field(name="Position", value=channel.position, inline=True)
        embed.add_field(name="NSFW", value=channel.is_nsfw(), inline=True)
        embed.add_field(name="Slowmode", value=f"{channel.slowmode_delay}s", inline=True)
        embed.add_field(name="Parent Category", value=channel.category.name if channel.category else "None", inline=False)
        embed.add_field(name="Topic", value=channel.topic or "No topic.", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=['si', 'sinfo'])
    @commands.guild_only()
    async def serverinfo(self, ctx):
        """Gives information about the guild"""
        guild = ctx.guild
        embed = discord.Embed(title="Server Info", description=guild.name, color=discord.Color.blue(), timestamp=ctx.message.created_at)
        embed.set_thumbnail(url=guild.icon)
        embed.add_field(name="Created at", value=f"<t:{int(guild.created_at.timestamp())}:F> (<t:{int(guild.created_at.timestamp())}:R>)", inline=True)
        embed.add_field(name="Owner", value=guild.owner, inline=True)
        embed.add_field(name="Description", value=guild.description or "No server description", inline=False)
        embed.add_field(name="Boost Info", value=f"Level {guild.premium_tier}\n{guild.premium_subscription_count}/14 boosts", inline=True)
        embed.add_field(name="Verification Level", value=str(guild.verification_level).capitalize(), inline=True)
        features_str = '\n'.join('✅ ' + f.replace('_', ' ').capitalize() for f in guild.features) or "None"
        embed.add_field(name="Server Features", value=features_str, inline=False)
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        embed.add_field(name="Channels", value=f"Total: {len(guild.channels)}\nText: {len(guild.text_channels)}\nVoice: {len(guild.voice_channels)}\nCategories: {len(guild.categories)}", inline=True)
        ban_count = len([entry async for entry in guild.bans()]) if ctx.guild.me.guild_permissions.ban_members else "N/A"
        embed.add_field(name="Ban count", value=str(ban_count), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Emojis", value=str(len(guild.emojis)), inline=True)
        embed.set_footer(text=f"Server ID: {guild.id} | Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=['rinfo'])
    @commands.guild_only()
    @app_commands.describe(role="The role to get information about.")
    async def roleinfo(self, ctx, *, role: discord.Role):
        """Displays information on a specified role"""
        creation_duration = datetime.datetime.now(pytz.UTC) - role.created_at
        years = creation_duration.days // 365
        months = (creation_duration.days % 365) // 30
        days = (creation_duration.days % 365) % 30
        embed = discord.Embed(title="Role Info", color=role.color)
        embed.description = f"Name: {role.name}\nMembers: {len(role.members)}\nColor: #{role.color.value:06x}\nCreated {years} years, {months} months, and {days} days ago"
        embed.set_footer(text=f"ID: {role.id}")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.guild_only()
    @app_commands.choices(option=[
        app_commands.Choice(name="Text", value="text"),
        app_commands.Choice(name="Voice", value="voice"),
        app_commands.Choice(name="Compare", value="compare")
    ])
    @app_commands.describe(option="Access type.", user="The user to check access of.", guild="The guild to check access of.")
    async def access(self, ctx, option: str, user: discord.Member = None, *, guild: discord.Guild = None):
        """Check channel access"""
        guild = guild or ctx.guild
        user = user or ctx.author
        if option.lower() == "text":
            channel_list = [c.name for c in guild.text_channels if c.permissions_for(user).read_messages]
            embed = discord.Embed(title=f'Text Channel Access - {user.name}', color=discord.Color.dark_embed())
            embed.add_field(name='Access', value=f'You have access to {len(channel_list)} out of {len(guild.text_channels)} text channels', inline=False)
            embed.add_field(name='Channels', value='\n'.join(channel_list) or "None", inline=False)
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.send(embed=embed)
        elif option.lower() == "voice":
            channel_list = [c.name for c in guild.voice_channels if c.permissions_for(user).connect]
            embed = discord.Embed(title=f'Voice Channel Access - {user.name}', color=discord.Color.dark_embed())
            embed.add_field(name='Access', value=f'You have access to {len(channel_list)} out of {len(guild.voice_channels)} voice channels', inline=False)
            embed.add_field(name='Channels', value='\n'.join(channel_list) or "None", inline=False)
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.send(embed=embed)
        elif option.lower() == "compare":
            author = ctx.author
            common_text = [c.name for c in guild.text_channels if c.permissions_for(author).read_messages and c.permissions_for(user).read_messages]
            author_only_text = [c.name for c in guild.text_channels if c.permissions_for(author).read_messages and not c.permissions_for(user).read_messages]
            user_only_text = [c.name for c in guild.text_channels if not c.permissions_for(author).read_messages and c.permissions_for(user).read_messages]
            common_voice = [c.name for c in guild.voice_channels if c.permissions_for(author).connect and c.permissions_for(user).connect]
            author_only_voice = [c.name for c in guild.voice_channels if c.permissions_for(author).connect and not c.permissions_for(user).connect]
            user_only_voice = [c.name for c in guild.voice_channels if not c.permissions_for(author).connect and c.permissions_for(user).connect]
            embed = discord.Embed(title=f'Access Comparison - {user.name}', color=discord.Color.dark_embed())
            embed.add_field(name=f'{len(common_text)} Text Channels in Common', value='\n'.join(common_text) or "None")
            embed.add_field(name='Text Channels You Have Exclusive Access To', value='\n'.join(author_only_text) or "None")
            embed.add_field(name=f'{user.name} Has Exclusive Access To', value='\n'.join(user_only_text) or "None")
            embed.add_field(name=f'{len(common_voice)} Voice Channels in Common', value='\n'.join(common_voice) or "None")
            embed.add_field(name='Voice Channels You Have Exclusive Access To', value='\n'.join(author_only_voice) or "None")
            embed.add_field(name=f'{user.name} Has Exclusive Access To', value='\n'.join(user_only_voice) or "None")
            embed.set_footer(text=f"Requested by {author.name}", icon_url=author.avatar.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Invalid option. Please use 'text', 'voice', or 'compare'.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @app_commands.describe(member="The user to check when they joined the server.")
    async def joined(self, ctx, member: Optional[discord.Member] = None):
        """Shows when a user joined the guild"""
        member = member or ctx.author
        embed = discord.Embed(description=f"{member.mention} joined this guild on <t:{int(member.joined_at.timestamp())}:f> (<t:{int(member.joined_at.timestamp())}:R>)", 
                             timestamp=ctx.message.created_at, color=discord.Color.blue())
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="firstmessage")
    @commands.guild_only()
    @app_commands.describe(channel="The channel to check the first message of.")
    async def first_message(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Shows the first message in a channel"""
        channel = channel or ctx.channel
        async for message in channel.history(limit=1, oldest_first=True):
            embed = discord.Embed(title="First Message", description=f"{message.content}\n[Jump to Message]({message.jump_url})", 
                                 timestamp=message.created_at, color=discord.Color.blue())
            embed.set_author(name=message.author.name, icon_url=message.author.avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.send(embed=embed)
            break
        else:
            await ctx.send("No messages found in this channel.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_emojis=True)
    @app_commands.describe(emoji_or_url="Emoji or url to import.", name="Name to set imported emoji to.")
    async def importemoji(self, ctx, emoji_or_url: str, name: str):
        """Import an emoji from another server or an image URL"""
        if emoji_or_url.startswith('http'):
            response = requests.get(emoji_or_url)
            if response.status_code == 200:
                emoji_name = name or 'emoji'
                emoji = await ctx.guild.create_custom_emoji(name=emoji_name, image=response.content)
                await ctx.send(f'Emoji `{emoji_name}` imported successfully: {emoji}')
            else:
                await ctx.send(f'Failed to retrieve image: {response.status_code}', ephemeral=True)
        else:
            emoji = discord.utils.get(self.bot.emojis, name=emoji_or_url)
            if emoji:
                emoji_name = name or emoji.name
                emoji = await ctx.guild.create_custom_emoji(name=emoji_name, image=await emoji.url.read())
                await ctx.send(f'Emoji `{emoji_name}` imported successfully: {emoji}')
            else:
                await ctx.send(f'Emoji `{emoji_or_url}` not found.', ephemeral=True)

    @commands.hybrid_command(name="messages")
    @commands.guild_only()
    @app_commands.describe(user="The user to check message count of.", channel="The channel to check messages of.")
    async def messages(self, ctx, user: Optional[discord.Member] = None, channel: Optional[discord.TextChannel] = None):
        """Counts the number of messages sent by a user in the server or a specified channel"""
        user = user or ctx.author
        if not ctx.guild.me.guild_permissions.read_message_history:
            await ctx.send("I don't have permission to read message history.", ephemeral=True)
            return
        initial_message = await ctx.send(f"Counting messages for **{user.display_name}**... This might take a while.")
        message_count = 0
        if channel:
            async for message in channel.history(limit=None):
                if message.author == user:
                    message_count += 1
        else:
            for chan in ctx.guild.text_channels:
                try:
                    async for message in chan.history(limit=None):
                        if message.author == user:
                            message_count += 1
                except discord.Forbidden:
                    continue
        embed = discord.Embed(title="Message Count", color=discord.Color.blue())
        if channel:
            embed.add_field(name="User", value=user.display_name, inline=True)
            embed.add_field(name="Channel", value=channel.mention, inline=True)
            embed.add_field(name="Messages", value=f"{message_count} messages", inline=True)
        else:
            embed.add_field(name="User", value=user.display_name, inline=True)
            embed.add_field(name="Server", value=ctx.guild.name, inline=True)
            embed.add_field(name="Messages", value=f"{message_count} messages", inline=True)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await initial_message.edit(content=None, embed=embed)

    @commands.hybrid_command()
    async def randomcolor(self, ctx):
        """Generates a random hex color with preview"""
        color = ''.join(random.choice('0123456789ABCDEF') for _ in range(6))
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        embed = discord.Embed(title="", color=int(color, 16))
        embed.add_field(name="Hex", value=f"#{color}", inline=False)
        embed.add_field(name="RGB", value=f"({r}, {g}, {b})", inline=False)
        embed.set_thumbnail(url=f"https://dummyimage.com/200x200/{color}/ffffff&text=+")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.guild_only()
    async def membercount(self, ctx):
        """Get the server member count"""
        embed = discord.Embed(title="Members", description=str(ctx.guild.member_count), color=discord.Color.dark_embed(), timestamp=ctx.message.created_at)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='quote')
    @commands.guild_only()
    @app_commands.describe(message_id="Message ID of message to quote.")
    async def quote(self, ctx, message_id: int):
        """Quotes a specific message by its ID"""
        try:
            message = await ctx.channel.fetch_message(message_id)
            embed = discord.Embed(title=f"Quote from {message.author.name}", description=message.content, color=discord.Color.green(), timestamp=message.created_at)
            embed.set_footer(text=f"Quoted by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.url.lower().endswith(('.png', '.jpeg', '.jpg', '.gif')):
                        embed.set_image(url=attachment.url)
                    else:
                        embed.add_field(name="Attachment", value=f"[{attachment.filename}]({attachment.url})", inline=False)
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send(f"Message with ID {message_id} not found.", ephemeral=True)

    @commands.hybrid_command(name='remind', aliases=['reminder'])
    @app_commands.describe(duration="When Luniren should remind you.", reminder="What Luniren should remind you of.")
    async def remind(self, ctx, duration: str, *, reminder: str):
        """Set a reminder for a specific time"""
        duration = duration.lower()
        if duration.endswith('s'):
            delay = int(duration[:-1])
        elif duration.endswith('m'):
            delay = int(duration[:-1]) * 60
        elif duration.endswith('h'):
            delay = int(duration[:-1]) * 3600
        else:
            await ctx.send('Invalid duration specified. Please use a valid format (e.g. 5s, 10m, 1h).', ephemeral=True)
            return
        await ctx.send(f'Okay, I will remind you in {duration}.')
        await asyncio.sleep(delay)
        embed = discord.Embed(title='Reminder', description=reminder, color=discord.Color.green())
        embed.set_footer(text='This is your reminder.')
        try:
            await ctx.author.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(f"{ctx.author.mention}, I couldn't send you a DM. Please enable DMs from server members to receive reminders.", ephemeral=True)


    @commands.hybrid_command()
    @app_commands.describe(link="Link to get destination of.")
    async def redirect(self, ctx, link: str):
        """Get the destination of any shortened or suspicious links you may not want to follow directly"""
       
        parsed_url = urllib.parse.urlparse(link)
        if not parsed_url.scheme:
            link = f"https://{link}"
        elif parsed_url.scheme not in ("http", "https"):
            await ctx.send("Invalid URL scheme. Please provide an HTTP or HTTPS URL.", ephemeral=True)
            return

        try:
            
            session = requests.Session()
            session.max_redirects = 10  
            response = session.head(link, allow_redirects=True, timeout=5)

            
            final_url = response.url
            redirect_count = len(response.history)

            
            if redirect_count == 0:
                await ctx.send(f"{link} does not redirect (direct link).", ephemeral=True)
            else:
                await ctx.send(f"{link} redirects to {final_url} after {redirect_count} redirect{'s' if redirect_count != 1 else ''}.", ephemeral=True)
        
        except requests.exceptions.InvalidSchema:
            await ctx.send("Invalid URL format. Please provide a valid HTTP or HTTPS URL.", ephemeral=True)
        except requests.exceptions.TooManyRedirects:
            await ctx.send("Too many redirects. The URL may be misconfigured or unsafe.", ephemeral=True)
        except requests.exceptions.Timeout:
            await ctx.send("Request timed out. The URL may be unreachable.", ephemeral=True)
        except requests.exceptions.RequestException as e:
            await ctx.send(f"Error resolving URL: {str(e)}", ephemeral=True)



    @commands.hybrid_command()
    @commands.guild_only()
    @app_commands.describe(
        option="Access type. (Text, Voice or Compare)",
        user="The user you want to check access of. ",
        guild="The server you want ot check the user's access in."
    )
    @app_commands.choices(
        option=[
            Choice(name="Text", value="text"),
            Choice(name="Voice", value="voice"),
            Choice(name="Compare", value="compare")
        ]
    )
    async def access(self, ctx, option: str, user:discord.Member = None, *, guild:discord.Guild = None):
        """Check channel access"""
        if option.lower() == "text":
            guild = guild or ctx.guild
            user = user or ctx.author
            channel_list = [c.name for c in guild.text_channels if c.permissions_for(user).read_messages]
            embed = Embed(title=f'Text Channel Access - {user.name}', color=discord.Color.dark_embed())
            embed.add_field(name='Access', value=f'You have access to {len(channel_list)} out of {len(guild.text_channels)} text channels', inline=False)
            embed.add_field(name='Channels', value='\n'.join(channel_list), inline=False)
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            
            await ctx.send(embed=embed)

        elif option.lower() == "voice":
            guild = guild or ctx.guild
            user = user or ctx.author
            channel_list = [c.name for c in guild.voice_channels if c.permissions_for(user).connect]
            
            embed = Embed(title=f'Voice Channel Access - {user.name}', color=discord.Color.dark_embed())
            embed.add_field(name='Access', value=f'You have access to {len(channel_list)} out of {len(guild.voice_channels)} voice channels', inline=False) 
            embed.add_field(name='Channels', value='\n'.join(channel_list), inline=False)
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            
            await ctx.send(embed=embed)

        elif option.lower() == "compare":
            guild = ctx.guild
            author = ctx.author
            common_text = [c.name for c in guild.text_channels 
                        if c.permissions_for(author).read_messages and c.permissions_for(user).read_messages]
            author_only_text = [c.name for c in guild.text_channels
                            if c.permissions_for(author).read_messages and not c.permissions_for(user).read_messages]  
            compared_only_text = [c.name for c in guild.text_channels
                            if not c.permissions_for(author).read_messages and c.permissions_for(user).read_messages]  
            common_voice = [c.name for c in guild.voice_channels 
                        if c.permissions_for(author).connect and c.permissions_for(user).connect]          
            author_only_voice = [c.name for c in guild.voice_channels 
                            if c.permissions_for(author).connect and not c.permissions_for(user).connect]
            compared_only_voice = [c.name for c in guild.voice_channels 
                                if not c.permissions_for(author).connect and c.permissions_for(user).connect]
            
            embed = Embed(title=f'Access Comparison - {user.name}', color=discord.Color.dark_embed())    
            embed.add_field(name=f'{len(common_text)} Text Channels in Common', value='\n'.join(common_text))
            embed.add_field(name='Text Channels You Have Exclusive Access To', value='\n'.join(author_only_text))
            embed.add_field(name=f'{user.name} Has Exclusive Access To', value='\n'.join(compared_only_text))
            embed.add_field(name=f'{len(common_voice)} Voice Channels in Common', value='\n'.join(common_voice)) 
            embed.add_field(name='Voice Channels You Have Exclusive Access To', value='\n'.join(author_only_voice))
            embed.add_field(name=f'{user.name} Has Exclusive Access To', value='\n'.join(compared_only_voice))
            embed.set_footer(text=f"Requested by {author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            
            await ctx.send(embed=embed)

        else:
            await ctx.send("Invalid option. Please use either 'text', 'voice', or 'compare'.", ephemeral=True)




    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(count="Number of members to display (1-25)")
    async def oldest(self, ctx, count: int = 5):
        """Tells you the oldest members of the server by account age."""
     
        if count < 1 or count > 25:
            await ctx.send("Count must be between 1 and 25.", ephemeral=True)
            return

        
        members = sorted(ctx.guild.members, key=lambda m: m.created_at)[:count]

        
        if not members:
            await ctx.send("No members found in this server.")
            return

   
        embed = discord.Embed(
            title="Old Members",
            color=discord.Color.dark_embed(),
            timestamp=ctx.message.created_at
        )

       
        def format_time_delta(dt):
            now = datetime.datetime.now(pytz.utc)
            delta = relativedelta(now, dt)
            years = delta.years
            months = delta.months
            days = delta.days
            hours = delta.hours
            if years > 0:
                return f"{years} year{'s' if years != 1 else ''}, {months} month{'s' if months != 1 else ''} and {days} day{'s' if days != 1 else ''} ago"
            elif months > 0:
                return f"{months} month{'s' if months != 1 else ''}, {days} day{'s' if days != 1 else ''} and {hours} hour{'s' if hours != 1 else ''} ago"
            else:
                return f"{days} day{'s' if days != 1 else ''} and {hours} hour{'s' if hours != 1 else ''} ago"

  
        description = ""
        for member in members:
            joined_ago = format_time_delta(member.joined_at)
            created_ago = format_time_delta(member.created_at)
            description += (
                f"**{member} ({member.id})**\n"
                f"Joined {joined_ago}\n"
                f"Created {created_ago}\n\n"
            )

        embed.description = description
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
        )

        await ctx.send(embed=embed)

    @oldest.error
    async def oldest_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need the 'Manage Messages' permission to use this command.", ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Please provide a number between 1 and 25.", ephemeral=True)
        else:
            await ctx.send(f"An error occurred: {str(error)}", ephemeral=True)        


    
    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(count="Number of members to display (1-25)")
    async def youngest(self, ctx, count: int = 5):
        """Tells you the youngest members of the server by account age."""
     
        if count < 1 or count > 25:
            await ctx.send("Count must be between 1 and 25.", ephemeral=True)
            return


        members = sorted(ctx.guild.members, key=lambda m: m.created_at, reverse=True)[:count]


        if not members:
            await ctx.send("No members found in this server.")
            return

   
        embed = discord.Embed(
            title="New Members",
            color=discord.Color.dark_embed(),
            timestamp=ctx.message.created_at
        )

       
        def format_time_delta(dt):
            now = datetime.datetime.now(pytz.utc)
            delta = relativedelta(now, dt) 
            years = delta.years
            months = delta.months
            days = delta.days
            hours = delta.hours
            if years > 0:
                return f"{years} year{'s' if years != 1 else ''}, {months} month{'s' if months != 1 else ''} and {days} day{'s' if days != 1 else ''} ago"
            elif months > 0:
                return f"{months} month{'s' if months != 1 else ''}, {days} day{'s' if days != 1 else ''} and {hours} hour{'s' if hours != 1 else ''} ago"
            else:
                return f"{days} day{'s' if days != 1 else ''} and {hours} hour{'s' if hours != 1 else ''} ago"

  
        description = ""
        for member in members:
            joined_ago = format_time_delta(member.joined_at)
            created_ago = format_time_delta(member.created_at)
            description += (
                f"**{member} ({member.id})**\n"
                f"Joined {joined_ago}\n"
                f"Created {created_ago}\n\n"
            )

        embed.description = description
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
        )

        await ctx.send(embed=embed)

    @youngest.error
    async def youngest_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need the 'Manage Messages' permission to use this command.", ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Please provide a number between 1 and 25.", ephemeral=True)
        else:
            await ctx.send(f"An error occurred: {str(error)}", ephemeral=True)        



    @commands.hybrid_command()
    @commands.guild_only()
    async def snipe(self, ctx):
        """Recall messages that are deleted"""
        guild_snipes = self.sniped_messages.get(ctx.guild.id, [])
        if not guild_snipes:
            await ctx.send("No recently deleted messages found in this server.", ephemeral=True)
            return
        message, deletion_time = guild_snipes[-1]
        embed = discord.Embed(color=discord.Color(0x36393f))
        embed.set_author(name=f"{message.author.name} ({message.author.id})", icon_url=message.author.avatar.url)
        embed.add_field(name=f"Message Contents (Sent <t:{int(message.created_at.timestamp())}:R>)", value=message.content or "*Empty message*", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Deleted At", value=f"<t:{int(deletion_time.replace(tzinfo=pytz.UTC).timestamp())}:R>", inline=True)
        embed.set_footer(text=f"Sniped in {ctx.guild.name}", icon_url=ctx.guild.icon)
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=['esnipe'])
    @commands.guild_only()
    async def editsnipe(self, ctx):
        """Recall messages that are edited"""
        guild_edits = self.edited_messages.get(ctx.guild.id, [])
        if not guild_edits:
            await ctx.send("No recently edited messages found in this server.", ephemeral=True)
            return
        before_message, after_message, edit_time = guild_edits[-1]
        editor = before_message.author if before_message.author.id == after_message.author.id else f"{before_message.author.name} (now {after_message.author.name})"
        embed = discord.Embed(color=discord.Color(0x36393f))
        embed.set_author(name=f"{editor} ({before_message.author.id})", icon_url=before_message.author.avatar.url)
        embed.add_field(name="Before", value=before_message.content or "*Empty message*", inline=False)
        embed.add_field(name="After", value=after_message.content or "*Empty message*", inline=False)
        embed.add_field(name="Edited At", value=f"<t:{int(edit_time.replace(tzinfo=pytz.UTC).timestamp())}:R>")
        embed.set_footer(text=f"Sniped in {ctx.guild.name}", icon_url=ctx.guild.icon)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.guild_only()
    @app_commands.describe(reason="Reason for AFK")
    async def afk(self, ctx, *, reason: str = "AFK"):
        """Set your AFK status"""
        if ctx.author.id in self.afk_users:
            await ctx.send("You are already AFK!", ephemeral=True)
            return
        self.afk_users[ctx.author.id] = {"reason": reason, "timestamp": datetime.datetime.now(pytz.UTC)}
        afk_nick = f"[AFK] {ctx.author.display_name}"
        await ctx.author.edit(nick=afk_nick)
        await ctx.send(f"{ctx.author.mention} You are now AFK. Reason: {reason}")



    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return
        now = datetime.datetime.now(pytz.UTC)
        if message.guild.id not in self.sniped_messages:
            self.sniped_messages[message.guild.id] = []
        self.sniped_messages[message.guild.id].append((message, now))
        if len(self.sniped_messages[message.guild.id]) > 10:
            self.sniped_messages[message.guild.id].pop(0)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        now = datetime.datetime.now(pytz.UTC)
        if before.guild.id not in self.edited_messages:
            self.edited_messages[before.guild.id] = []
        self.edited_messages[before.guild.id].append((before, after, now))
        if len(self.edited_messages[before.guild.id]) > 10:
            self.edited_messages[before.guild.id].pop(0)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return
        if message.author.id in self.afk_users:
            afk_data = self.afk_users.pop(message.author.id)
            afk_nick = message.author.display_name.replace("[AFK] ", "")
            await message.author.edit(nick=afk_nick)
            afk_time = datetime.datetime.now(pytz.UTC) - afk_data["timestamp"]
            await message.channel.send(f"Welcome back, {message.author.mention}! You are no longer AFK. (Away for {precisedelta(afk_time)})")
        for mention in message.mentions:
            if mention.id in self.afk_users:
                afk_data = self.afk_users[mention.id]
                afk_time = datetime.datetime.now(pytz.UTC) - afk_data["timestamp"]
                await message.channel.send(f"{mention.mention} is currently AFK. Reason: {afk_data['reason']} (Last seen {precisedelta(afk_time)} ago)")



async def setup(bot):
    await bot.add_cog(Utility(bot))