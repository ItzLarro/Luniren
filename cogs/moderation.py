import discord
import asyncio 
import string
import random 
import datetime 
import humanize
import requests
import re
import logging
import contextlib
import json
import pytz
import typing
import time
import os
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



import datetime
class TimeIntervalConverter(commands.Converter):
    async def convert(self, ctx, argument):
        interval_regex = re.compile(
            r"^(?:(?P<years>\d+)y)?(?:(?P<months>\d+)mo)?(?:(?P<weeks>\d+)w)?(?:(?P<days>\d+)d)?(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$"
        )

        match = interval_regex.match(argument)
        if not match:
            raise commands.BadArgument("Invalid time interval. Examples: 4h, 3m, 10s", ephemeral=True)

        groups = match.groupdict(default="0")
        years = int(groups["years"])
        months = int(groups["months"])
        weeks = int(groups["weeks"])
        days = int(groups["days"])
        hours = int(groups["hours"])
        minutes = int(groups["minutes"])
        seconds = int(groups["seconds"])

        # Convert months to days by approximating 30.436875 days per month
        total_days = (
            years * 365
            + months * 30.436875
            + weeks * 7
            + days
        )

        delta = timedelta(
            days=int(total_days),
            hours=hours,
            minutes=minutes,
            seconds=seconds,
        )

        return delta


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.modlog_channel_id = None  # Set this to your modlog channel ID or fetch dynamically

    async def log_action(self, guild, action, moderator, target, reason=None):
        if not self.modlog_channel_id:
            return
        modlog_channel = guild.get_channel(self.modlog_channel_id)
        if not modlog_channel:
            return
        embed = discord.Embed(
            title=action,
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(pytz.UTC)
        )
        embed.add_field(name="Moderator", value=moderator.mention, inline=True)
        embed.add_field(name="Target", value=target.mention if isinstance(target, discord.Member) else str(target), inline=True)
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        try:
            await modlog_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.hybrid_command(aliases=["sm"])
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(interval="Interval for slowmode. Example: 20s or 1m or 2m30s or 5h40m2s")
    async def slowmode(self, ctx, interval: TimeIntervalConverter = datetime.timedelta(seconds=0)):
        """Changes channel's slowmode setting. Interval can be 0s to 6h. Use without parameters to disable."""
        seconds = int(interval.total_seconds())
        if seconds > 21600:
            await ctx.send("Slowmode cannot exceed 6 hours.", ephemeral=True)
            return
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds > 0:
            interval_str = precisedelta(interval, format="%0.0f", suppress=["microseconds"])
            await ctx.send(f"Slowmode interval is now {interval_str}.")
        else:
            await ctx.send("Slowmode has been disabled.")
        await self.log_action(ctx.guild, "Slowmode Set", ctx.author, ctx.channel, f"Interval: {seconds}s")

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(member="User you want to kick.", reason="Reason for kick.")
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """Kick a user from the server."""
        if ctx.author == member:
            await ctx.send("You cannot kick yourself.", ephemeral=True)
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot kick someone with a higher or equal role.", ephemeral=True)
            return
        try:
            embed = discord.Embed(
                title="Kicked",
                description=f"You have been kicked from {ctx.guild.name}.",
                color=discord.Color.red(),
                timestamp=ctx.message.created_at
            )
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            invite = await ctx.channel.create_invite()
            embed.add_field(name="Rejoin", value=f"[Click here]({invite})", inline=False)
            await member.send(embed=embed)
        except discord.HTTPException:
            pass
        try:
            await ctx.guild.kick(member, reason=reason)
            await ctx.send(f"Kicked **{member.name}**.")
            await self.log_action(ctx.guild, "Kick", ctx.author, member, reason)
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick this member.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="The user you want to ban.", reason="Reason for ban.")
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban a user from the server."""
        if ctx.author == member:
            await ctx.send("You cannot ban yourself.", ephemeral=True)
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot ban someone with a higher or equal role.", ephemeral=True)
            return
        try:
            embed = discord.Embed(
                title="Banned",
                description=f"You have been banned from {ctx.guild.name}.",
                color=discord.Color.red(),
                timestamp=ctx.message.created_at
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            await member.send(embed=embed)
        except discord.HTTPException:
            pass
        try:
            await ctx.guild.ban(member, reason=reason)
            await ctx.send(f"Banned **{member.name}**. Reason: {reason}")
            await self.log_action(ctx.guild, "Ban", ctx.author, member, reason)
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban this member.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(user="User to unban.", reason="Reason for unban.")
    async def unban(self, ctx, user: discord.User, *, reason: str = None):
        """Unban a user from the server."""
        try:
            invite = await ctx.channel.create_invite()
            embed = discord.Embed(
                title="Unbanned",
                description=f"You have been unbanned from {ctx.guild.name}.",
                color=discord.Color.green(),
                timestamp=ctx.message.created_at
            )
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Rejoin", value=f"[Click here]({invite})", inline=False)
            await user.send(embed=embed)
        except discord.HTTPException:
            pass
        try:
            await ctx.guild.unban(user, reason=reason)
            await ctx.send(f"Unbanned **{user.name}**. Reason: {reason or 'None'}")
            await self.log_action(ctx.guild, "Unban", ctx.author, user, reason)
        except discord.NotFound:
            await ctx.send("This user is not banned.", ephemeral=True)
        except discord.Forbidden:
            await ctx.send("I don't have permission to unban this user.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="The user you want to mute.", reason="Reason for mute.")
    async def mute(self, ctx, member: discord.Member, *, reason: str = None):
        """Mutes a user by assigning the Muted role."""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, speak=False)
        if muted_role in member.roles:
            await ctx.send(f"{member.mention} is already muted.", ephemeral=True)
            return
        try:
            await member.add_roles(muted_role, reason=reason)
            await ctx.send(f"Muted **{member.mention}**. Reason: {reason or 'None'}")
            await self.log_action(ctx.guild, "Mute", ctx.author, member, reason)
        except discord.Forbidden:
            await ctx.send("I don't have permission to mute this member.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="User to unmute.")
    async def unmute(self, ctx, member: discord.Member):
        """Unmutes a user by removing the Muted role."""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role or muted_role not in member.roles:
            await ctx.send(f"{member.mention} is not muted.", ephemeral=True)
            return
        try:
            await member.remove_roles(muted_role)
            await ctx.send(f"Unmuted **{member.mention}**.")
            await self.log_action(ctx.guild, "Unmute", ctx.author, member)
        except discord.Forbidden:
            await ctx.send("I don't have permission to unmute this member.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(
        member="User to temporarily mute.",
        duration="The duration of mute. Example: 1h or 2h3m or 2d5h or 4w5h or 6mo or 3y or 1y3mo2w3d4h5m2s",
        reason="Reason for mute." 
    )
    async def tempmute(self, ctx, member: discord.Member, duration: TimeIntervalConverter, *, reason: str = None):
        """Temporarily mutes a user for the specified duration."""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, speak=False)
        if muted_role in member.roles:
            await ctx.send(f"{member.mention} is already muted.", ephemeral=True)
            return
        duration_seconds = int(duration.total_seconds())
        try:
            await member.add_roles(muted_role, reason=reason)
            await ctx.send(f"Muted **{member.mention}** for {precisedelta(duration, format='%0.0f')}. Reason: {reason or 'None'}")
            await self.log_action(ctx.guild, "Temp Mute", ctx.author, member, f"Duration: {duration_seconds}s, Reason: {reason}")
            await asyncio.sleep(duration_seconds)
            if muted_role in member.roles:
                await member.remove_roles(muted_role)
                await ctx.send(f"Unmuted **{member.mention}** (temp mute expired).")
                await self.log_action(ctx.guild, "Temp Mute Expired", ctx.author, member)
        except discord.Forbidden:
            await ctx.send("I don't have permission to mute this member.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(
        member="User to temporarily ban.",
        duration="The duration of ban. Example: 1h or 2h3m or 2d5h or 4w5h or 6mo or 3y or 1y3mo2w3d4h5m2s",
        days="Days worth of messages to delete.",
        reason="Reason for ban."
    )
    async def tempban(self, ctx, member: discord.Member, duration: TimeIntervalConverter, days: Optional[int] = 0, *, reason: str = None):
        """Temporarily ban a user from the server."""
        if ctx.author == member:
            await ctx.send("You cannot ban yourself.", ephemeral=True)
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot ban someone with a higher or equal role.", ephemeral=True)
            return
        if not (0 <= days <= 7):
            await ctx.send("Days must be between 0 and 7.", ephemeral=True)
            return
        delete_message_seconds = days * 86400
        duration_seconds = int(duration.total_seconds())
        unban_time = int((datetime.datetime.now(pytz.UTC) + duration).timestamp())
        try:
            embed = discord.Embed(
                title="Temp Banned",
                description=f"You have been temporarily banned from {ctx.guild.name} until <t:{unban_time}:F>.",
                color=discord.Color.red(),
                timestamp=ctx.message.created_at
            )
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            await member.send(embed=embed)
        except discord.HTTPException:
            pass
        try:
            await ctx.guild.ban(member, reason=reason, delete_message_seconds=delete_message_seconds)
            await ctx.send(f"Temporarily banned **{member.name}** until <t:{unban_time}:F>. Reason: {reason or 'None'}")
            await self.log_action(ctx.guild, "Temp Ban", ctx.author, member, f"Duration: {duration_seconds}s, Days: {days}, Reason: {reason}")
            await asyncio.sleep(duration_seconds)
            await ctx.guild.unban(member)
            embed = discord.Embed(
                title="Temp Ban Expired",
                description=f"Your temporary ban in {ctx.guild.name} has expired.",
                color=discord.Color.green()
            )
            invite = await ctx.channel.create_invite()
            embed.add_field(name="Rejoin", value=f"[Click here]({invite})", inline=False)
            await member.send(embed=embed)
            await self.log_action(ctx.guild, "Temp Ban Expired", ctx.author, member)
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban this member.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="User to softban.", reason="Reason for softban.")
    async def softban(self, ctx, member: discord.Member, *, reason: str = None):
        """Kick a user and delete 1 day's worth of their messages."""
        if ctx.author == member:
            await ctx.send("You cannot softban yourself.", ephemeral=True)
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot softban someone with a higher or equal role.", ephemeral=True)
            return
        try:
            embed = discord.Embed(
                title="Soft Banned",
                description=f"You have been soft banned from {ctx.guild.name} to clear your messages.",
                color=discord.Color.red(),
                timestamp=ctx.message.created_at
            )
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            invite = await ctx.channel.create_invite()
            embed.add_field(name="Rejoin", value=f"[Click here]({invite})", inline=False)
            await member.send(embed=embed)
        except discord.HTTPException:
            pass
        try:
            await ctx.guild.ban(member, reason=reason, delete_message_seconds=86400)
            await ctx.guild.unban(member)
            await ctx.send(f"Soft banned **{member.name}**. Reason: {reason or 'None'}")
            await self.log_action(ctx.guild, "Soft Ban", ctx.author, member, reason)
        except discord.Forbidden:
            await ctx.send("I don't have permission to softban this member.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(user_id="The id of the user to hackban.", reason="Reason for hackban.")
    async def hackban(self, ctx, user_id: str, *, reason: str = None):
        """Bans a user who is not in the server by their ID."""
        try:
            user_id = int(user_id)
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.ban(user, reason=reason)
            await ctx.send(f"Banned **{user.name}** (ID: {user.id}). Reason: {reason or 'None'}")
            await self.log_action(ctx.guild, "Hack Ban", ctx.author, user, reason)
        except ValueError:
            await ctx.send("Invalid user ID. Please provide a valid integer.", ephemeral=True)
        except discord.NotFound:
            await ctx.send("User not found.", ephemeral=True)
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban this user.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @app_commands.describe(members="The mention or ids of users to ban. (Sperated by space)", reason="Reason for massban.")
    async def massban(self, ctx, members: commands.Greedy[Union[discord.Member, int]], *, reason: str = None):
        """Bans multiple members by their ID or mention."""
        if not members:
            await ctx.send("Please provide member IDs or mentions to ban.", ephemeral=True)
            return
        banned = []
        for member in members:
            try:
                if isinstance(member, discord.Member):
                    if member.top_role >= ctx.author.top_role:
                        continue
                    await ctx.guild.ban(member, reason=reason)
                    banned.append(f"{member.name} ({member.id})")
                else:
                    user = await self.bot.fetch_user(member)
                    await ctx.guild.ban(user, reason=reason)
                    banned.append(f"{user.name} ({user.id})")
            except discord.HTTPException:
                continue
        if banned:
            embed = discord.Embed(title="Mass Ban", color=discord.Color.red())
            embed.add_field(name="Banned Members", value="\n".join(banned), inline=False)
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "Mass Ban", ctx.author, ", ".join(banned), reason)
        else:
            await ctx.send("No members were banned.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @app_commands.describe(args="The ids of users to massunban.", reason="Reason for massunban.")
    async def massunban(self, ctx, *, args: str = None, reason: str = None):
        """Unban all users or users with a specific ban reason."""
        
        user_ids = []
        if args and args.split()[-1].startswith("reason="):
            reason = args.split()[-1][7:]
            args = " ".join(args.split()[:-1])
        if args:
            for arg in args.split():
                user_id = arg.strip("<@!>")
                if user_id.isnumeric():
                    user_ids.append(int(user_id))
        banned_users = [entry.user async for entry in ctx.guild.bans()]
        if not user_ids:
            unbanned = []
            for user in banned_users:
                try:
                    await ctx.guild.unban(user, reason=reason)
                    unbanned.append(f"{user.name} ({user.id})")
                except discord.HTTPException:
                    continue
            if unbanned:
                embed = discord.Embed(title="Mass Unban", description="All users have been unbanned.", color=discord.Color.green())
                embed.add_field(name="Unbanned Users", value="\n".join(unbanned), inline=False)
                if reason:
                    embed.add_field(name="Reason", value=reason, inline=False)
                await ctx.send(embed=embed)
                await self.log_action(ctx.guild, "Mass Unban", ctx.author, ", ".join(unbanned), reason)
            else:
                await ctx.send("No users were unbanned.", ephemeral=True)
        else:
            unbanned = []
            for user_id in user_ids:
                try:
                    user = await self.bot.fetch_user(user_id)
                    for banned_user in banned_users:
                        if banned_user.id == user_id:
                            await ctx.guild.unban(user, reason=reason)
                            unbanned.append(f"{user.name} ({user.id})")
                            break
                except discord.HTTPException:
                    continue
            if unbanned:
                embed = discord.Embed(title="Mass Unban", description="The following users have been unbanned:", color=discord.Color.green())
                embed.add_field(name="Unbanned Users", value="\n".join(unbanned), inline=False)
                if reason:
                    embed.add_field(name="Reason", value=reason, inline=False)
                await ctx.send(embed=embed)
                await self.log_action(ctx.guild, "Mass Unban", ctx.author, ", ".join(unbanned), reason)
            else:
                await ctx.send("No users were unbanned.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(member="User to warn.", reason="Reason for warn.")
    async def warn(self, ctx, member: discord.Member, *, reason: str = None):
        """Warns a user."""
        if ctx.author == member:
            await ctx.send("You cannot warn yourself.", ephemeral=True)
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot warn someone with a higher or equal role.", ephemeral=True)
            return
        try:
            embed = discord.Embed(
                title=f"Warned in {ctx.guild.name}",
                color=discord.Color.orange(),
                timestamp=ctx.message.created_at
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            await member.send(embed=embed)
        except discord.HTTPException:
            pass
        await ctx.send(f"Warned **{member.display_name}**. Reason: {reason or 'None'}")
        await self.log_action(ctx.guild, "Warn", ctx.author, member, reason)


#cleanup
    async def is_command_message(self, message, ctx):
        """Check if a message is a user command invoking the bot."""
        if message.author.bot:
            return False

        prefixes = await self.bot.get_prefix(ctx.message)
        if isinstance(prefixes, str):
            prefixes = [prefixes]
        for prefix in prefixes:
            if message.content.startswith(prefix):
                return True
  
        if message.content.startswith(f"</{self.bot.user.name.lower()}"):
            return True
        return False

    @commands.hybrid_command(aliases=["cu"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(limit="Number of bot messages to delete.")
    async def cleanup(self, ctx, limit: Optional[int] = 5):
        """Clears the most recent bot messages and related user command messages in the channel.
        
        Args:
            limit: Number of bot messages to delete (default: 5, optional).

        """
        if limit < 1:
            await ctx.send("Please specify a number greater than 0.", delete_after=5, ephemeral=True)
            return


        bot_message_count = 0
        messages_to_delete = []
        command_message_ids = set() 

        async for msg in ctx.channel.history(limit=100):  
         
            if msg.id == ctx.message.id:
                messages_to_delete.append(msg)
                continue

            if msg.author == self.bot.user and msg.id not in command_message_ids:
                bot_message_count += 1
                messages_to_delete.append(msg)
                command_message_ids.add(msg.id) 
                if bot_message_count >= limit:
                    break  


            elif await self.is_command_message(msg, ctx) and msg.id not in command_message_ids:
                messages_to_delete.append(msg)
                command_message_ids.add(msg.id)

    
        deleted_bot_count = sum(1 for msg in messages_to_delete if msg.author == self.bot.user)
        if messages_to_delete:
            await ctx.channel.delete_messages(messages_to_delete)
            await ctx.send(f"{deleted_bot_count} bot messages and related commands have been cleaned up.", delete_after=5)
            await self.log_action(ctx.guild, "Cleanup", ctx.author, ctx.channel, f"Deleted {deleted_bot_count} bot messages and related commands")





    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(limit="Number of messages to delete.", user="Optional user whose messages to delete.", contains="Optional string that messages must contain.")
    async def purge(self, ctx, limit: int = 100, user: Optional[discord.Member] = None, *, contains: Optional[str] = None):
        """Deletes a specified number of messages, optionally from a user or containing a string.

        Args:
            limit: Number of messages to delete (default: 100).
            user: Optional user whose messages to delete.
            contains: Optional string that messages must contain.
        """
        if limit < 1:
            await ctx.send("Please specify a number greater than 0.", delete_after=5, ephemeral=True)
            return

        def check(msg):
          
            if msg.id == ctx.message.id:
                return True
     
            if user and msg.author != user:
                return False
            if contains and contains.lower() not in msg.content.lower():
                return False
            return True

        filtered_count = 0
        messages_to_delete = []

 
        async for msg in ctx.channel.history(limit=limit + 1):  
            if check(msg):
                messages_to_delete.append(msg)
                if msg.id != ctx.message.id:
                    filtered_count += 1
                if filtered_count >= limit and ctx.message.id in [m.id for m in messages_to_delete]:
                    break


        if messages_to_delete:
            await ctx.channel.delete_messages(messages_to_delete)
            await ctx.send(f"{filtered_count} messages have been purged.", delete_after=5)
            await self.log_action(ctx.guild, "Purge", ctx.author, ctx.channel, f"Deleted {filtered_count} messages")
        else:
            await ctx.send("No messages matched the criteria.", delete_after=5, ephemeral=True)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def owner_purge(self, ctx, limit: int = 100, user: Optional[discord.Member] = None, *, contains: Optional[str] = None):
        """Owner-only purge command."""
        def check(msg):
            if user and msg.author != user:
                return False
            if contains and contains not in msg.content:
                return False
            return True
        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=limit, check=check)
        await ctx.send(f"{len(deleted)} messages have been purged.", delete_after=5)
        await self.log_action(ctx.guild, "Owner Purge", ctx.author, ctx.channel, f"Deleted {len(deleted)} messages")

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        """Locks the current channel."""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        embed = discord.Embed(
            title="🔒 Channel Locked",
            description=f"The channel has been locked by {ctx.author.mention}.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        await self.log_action(ctx.guild, "Channel Lock", ctx.author, ctx.channel)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        """Unlocks the current channel."""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        embed = discord.Embed(
            title="🔓 Channel Unlocked",
            description=f"The channel has been unlocked by {ctx.author.mention}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        await self.log_action(ctx.guild, "Channel Unlock", ctx.author, ctx.channel)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx):
        """Locks all channels in the server."""
        for channel in ctx.guild.text_channels:
            try:
                await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            except discord.Forbidden:
                continue
        embed = discord.Embed(title="Server Lockdown", description="🔒 The server has been locked down.", color=discord.Color.red())
        await ctx.send(embed=embed)
        await self.log_action(ctx.guild, "Server Lockdown", ctx.author, ctx.guild)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def unlockdown(self, ctx):
        """Unlocks all channels in the server."""
        for channel in ctx.guild.text_channels:
            try:
                await channel.set_permissions(ctx.guild.default_role, send_messages=True)
            except discord.Forbidden:
                continue
        embed = discord.Embed(title="Server Unlock", description="🔓 The server has been unlocked.", color=discord.Color.green())
        await ctx.send(embed=embed)
        await self.log_action(ctx.guild, "Server Unlock", ctx.author, ctx.guild)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(role="Role to allow channel viewing.")
    async def viewlock(self, ctx, role: discord.Role):
        """Locks the channel for viewing except for the specified role."""
        overwrites_everyone = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrites_everyone.view_channel = False
        overwrites_role = ctx.channel.overwrites_for(role)
        overwrites_role.view_channel = True
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrites_everyone)
        await ctx.channel.set_permissions(role, overwrite=overwrites_role)
        await ctx.send(f"{ctx.channel.mention} has been view-locked for {role.mention}.")
        await self.log_action(ctx.guild, "View Lock", ctx.author, ctx.channel, f"Role: {role.name}")

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def unviewlock(self, ctx):
        """Removes view lock from the channel."""
        overwrites_everyone = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrites_everyone.view_channel = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrites_everyone)
        await ctx.send(f"{ctx.channel.mention} view permissions reset to default.")
        await self.log_action(ctx.guild, "View Unlock", ctx.author, ctx.channel)

    @commands.hybrid_command(name="createchannel")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @app_commands.choices(
        channeltype=[
            app_commands.Choice(name="Text", value=0),
            app_commands.Choice(name="Voice", value=2),
            app_commands.Choice(name="Category", value=4),
            app_commands.Choice(name="News", value=5),
            app_commands.Choice(name="Stage", value=13),
            app_commands.Choice(name="Forum", value=15)
        ]
    )
    @app_commands.describe(
        channeltype="The type of channel to create",
        name="The name of the channel to create",
        category="The category to create the channel in",
        slowmode="Slowmode in seconds (0 to disable)"
    )
    async def create_channel(self, ctx, channeltype: int, name: str, category: Optional[discord.CategoryChannel] = None, slowmode: Optional[int] = 0):
        """Creates a new channel."""
        channel_type = discord.ChannelType(channeltype)
        try:
            channel = await ctx.guild.create_text_channel(
                name=name,
                category=category,
                slowmode_delay=slowmode if channel_type == discord.ChannelType.text else None
            ) if channel_type == discord.ChannelType.text else await ctx.guild.create_channel(name=name, channel_type=channel_type, category=category)
            embed = discord.Embed(
                description=f"✅ Created {channel_type.name} channel {channel.mention}",
                color=discord.Color.green()
            )
            if category:
                embed.add_field(name="Category", value=category.name, inline=True)
            if slowmode and channel_type == discord.ChannelType.text:
                embed.add_field(name="Slowmode", value=f"{slowmode} second{'s' if slowmode != 1 else ''}", inline=True)
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "Channel Created", ctx.author, channel, f"Type: {channel_type.name}, Name: {name}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to create channels.", ephemeral=True)

    @commands.hybrid_command(name="deletechannel")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel="Channel to delete.", reason="Reason for delete.")
    async def delete_channel(self, ctx, channel: discord.abc.GuildChannel, *, reason: str = None):
        """Deletes a channel."""
        try:
            channel_type = channel.type.name
            await channel.delete(reason=reason)
            embed = discord.Embed(
                description=f"✅ Deleted {channel_type} channel {channel.name}",
                color=discord.Color.green()
            )
            if reason:
                embed.add_field(name="Reason", value=reason, inline=True)
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "Channel Deleted", ctx.author, channel, reason)
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete this channel.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(
        name="Name of role.",
        color="Role color. Hex or color name.",
        mentionable="Allow anyone to mention this role. (True or False)",
        hoist="Display role members separately from online members. (True or False)"
    )
    async def createrole(self, ctx, name: str, color: str = None, mentionable: bool = False, hoist: bool = False):
        """Creates a new role."""
        COLOR_MAP = {
            "red": 0xFF0000, "blue": 0x3498db, "green": 0x2ecc71, "yellow": 0xFFFF00,
            "purple": 0x9b59b6, "orange": 0xe67e22, "turquoise": 0x1abc9c, "black": 0x000000, "white": 0xFFFFFF
        }
        def parse_color(color_str):
            if color_str and color_str.startswith('#') and len(color_str) == 7:
                return int(color_str[1:], 16)
            color_str = color_str.lower() if color_str else None
            return COLOR_MAP.get(color_str) if color_str in COLOR_MAP else None
        color_value = discord.Color(parse_color(color) or discord.Color.default().value)
        try:
            role = await ctx.guild.create_role(
                name=name, color=color_value, mentionable=mentionable, hoist=hoist, reason=f"Created by {ctx.author}"
            )
            embed = discord.Embed(title="Role Created", color=color_value)
            embed.description = f"Created role **{role.name}**.\nColor: {role.color}\nMentionable: {role.mentionable}\nHoisted: {role.hoist}"
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "Role Created", ctx.author, role, f"Name: {name}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to create roles.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(role="Role to delete.")
    async def deleterole(self, ctx, role: discord.Role):
        """Deletes a role."""
        if role >= ctx.author.top_role:
            await ctx.send("You cannot delete a role higher or equal to your top role.", ephemeral=True)
            return
        try:
            await role.delete()
            await ctx.send(f"Deleted role **{role.name}**.")
            await self.log_action(ctx.guild, "Role Deleted", ctx.author, role)
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete this role.", ephemeral=True)

    @commands.hybrid_command(aliases=["rank"])
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(role="Role to add or remove.", member="User to add or remove role from.")
    async def role(self, ctx, role: discord.Role, member: Optional[discord.Member] = None):
        """Add or remove a role from a user."""
        member = member or ctx.author
        if role >= ctx.author.top_role:
            await ctx.send("You cannot modify a role higher or equal to your top role.", ephemeral=True)
            return
        if role >= ctx.guild.me.top_role:
            await ctx.send("I cannot modify a role higher than my top role.", ephemeral=True)
            return
        try:
            if role in member.roles:
                await member.remove_roles(role)
                await ctx.send(f"Removed **{role.name}** from **{member.name}**.")
                await self.log_action(ctx.guild, "Role Removed", ctx.author, member, f"Role: {role.name}")
            else:
                await member.add_roles(role)
                await ctx.send(f"Added **{role.name}** to **{member.name}**.")
                await self.log_action(ctx.guild, "Role Added", ctx.author, member, f"Role: {role.name}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to modify roles for this member.", ephemeral=True)

    @commands.hybrid_command(aliases=["temprank"])
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="User to temporarily grant a role.", role="Role to grant temporarily.", duration="Duration for the role. (e.g., 5m, 2h, 1d, 2h3m, 4w, 4mo)")
    async def temprole(self, ctx, member: discord.Member, role: discord.Role, duration: str):
        """Temporarily adds a role to a user (e.g., 5m, 2h, 1d)."""
        if role >= ctx.author.top_role:
            await ctx.send("You cannot assign a role higher or equal to your top role.", ephemeral=True)
            return
        if role >= ctx.guild.me.top_role:
            await ctx.send("I cannot assign a role higher than my top role.", ephemeral=True)
            return
        time_converter = {"m": 60, "h": 3600, "d": 86400, "w": 604800, "mo": 2592000}
        try:
            duration_seconds = int(duration[:-1]) * time_converter[duration[-1].lower()]
            await member.add_roles(role)
            embed = discord.Embed(title="Temporary Role", color=discord.Color.green())
            embed.description = f"Added {role.mention} to {member.mention} for {duration}."
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "Temp Role Added", ctx.author, member, f"Role: {role.name}, Duration: {duration}")
            await asyncio.sleep(duration_seconds)
            if role in member.roles:
                await member.remove_roles(role)
                await ctx.send(f"Removed **{role.name}** from **{member.name}** (temp role expired).")
                await self.log_action(ctx.guild, "Temp Role Expired", ctx.author, member, f"Role: {role.name}")
        except (ValueError, KeyError):
            await ctx.send("Invalid duration format. Use <number><unit> (e.g., 5m, 2h, 1d, 1w, 1mo).", ephemeral=True)
        except discord.Forbidden:
            await ctx.send("I don't have permission to modify roles for this member.", ephemeral=True)

    @commands.hybrid_command(aliases=["setnick", "nick"])
    @commands.guild_only()
    @commands.has_permissions(manage_nicknames=True)
    @app_commands.describe(member="User to change nickname of.", nickname="Nickname to change to.")
    async def nickname(self, ctx, member: discord.Member, *, nickname: str = None):
        """Changes a user's nickname."""
        try:
            await member.edit(nick=nickname)
            action = f"Changed nickname of {member.mention} to {nickname}" if nickname else f"Reset nickname of {member.mention}"
            await ctx.send(action)
            await self.log_action(ctx.guild, "Nickname Changed", ctx.author, member, f"New nickname: {nickname or 'None'}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to change this member's nickname.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel="Channel to send announcement to.", message="Message to announce.", mention="Role to mention.")
    async def announcement(self, ctx, channel: Optional[discord.TextChannel], message: str, mention: Optional[discord.Role] = None):
        """Sends an announcement to a channel."""
        target_channel = channel or ctx.channel
        embed = discord.Embed(
            title="Announcement",
            description=message,
            color=discord.Color.blue(),
            timestamp=ctx.message.created_at
        )
        try:
            await target_channel.send(content=mention.mention if mention else None, embed=embed)
            await ctx.send(f"Announcement sent to {target_channel.mention}.", ephemeral=True)
            await self.log_action(ctx.guild, "Announcement", ctx.author, target_channel, f"Message: {message}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to send messages in that channel.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_nicknames=True)
    @app_commands.describe(member="User to decancer.", freeze="Keep it that way. (True or False)")
    async def decancer(self, ctx, member: discord.Member, freeze: bool = False):
        """Removes special characters from a user's nickname."""
        new_nickname = ''.join(c for c in member.display_name if c.isalnum() or c.isspace())
        try:
            await member.edit(nick=new_nickname)
            await ctx.send(f"Decancered nickname for **{member.name}**.")
            await self.log_action(ctx.guild, "Decancer", ctx.author, member, f"New nickname: {new_nickname}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to change this member's nickname.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_nicknames=True)
    @app_commands.describe(role="Role to dehoist.")
    async def dehoist(self, ctx, role: Optional[discord.Role] = None):
        """Removes special characters from nicknames of all members with a role."""
        role = role or ctx.guild.default_role
        decancered = []
        for member in ctx.guild.members:
            if role in member.roles:
                new_nickname = ''.join(c for c in member.display_name if c.isalnum() or c.isspace())
                try:
                    await member.edit(nick=new_nickname)
                    decancered.append(member.name)
                except discord.Forbidden:
                    continue
        if decancered:
            await ctx.send(f"Decancered nicknames for members with role **{role.name}**:\n{', '.join(decancered)}")
            await self.log_action(ctx.guild, "Dehoist", ctx.author, role, f"Members affected: {len(decancered)}")
        else:
            await ctx.send("No nicknames were changed.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel="Channel to clone.")
    async def clone(self, ctx, channel: discord.TextChannel):
        """Clones a text channel."""
        try:
            new_channel = await ctx.guild.create_text_channel(
                name=channel.name,
                category=channel.category,
                overwrites=channel.overwrites,
                topic=channel.topic,
                slowmode_delay=channel.slowmode_delay
            )
            await ctx.send(f"Cloned channel to {new_channel.mention}.")
            await self.log_action(ctx.guild, "Channel Cloned", ctx.author, channel, f"New channel: {new_channel.name}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to clone this channel.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel="Channel to rename.", new_name="New channel name.")
    async def rename(self, ctx, channel: discord.TextChannel, *, new_name: str):
        """Renames a channel."""
        try:
            await channel.edit(name=new_name)
            await ctx.send(f"Renamed channel to **{new_name}**.")
            await self.log_action(ctx.guild, "Channel Renamed", ctx.author, channel, f"New name: {new_name}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to rename this channel.", ephemeral=True)

    @commands.hybrid_command(aliases=["movech"])
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel="Channel to move.", category="Category to move channel to.")
    async def movechannel(self, ctx, channel: discord.TextChannel, category: discord.CategoryChannel):
        """Moves a channel to a category."""
        try:
            await channel.edit(category=category)
            await ctx.send(f"Moved {channel.mention} to category **{category.name}**.")
            await self.log_action(ctx.guild, "Channel Moved", ctx.author, channel, f"Category: {category.name}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to move this channel.", ephemeral=True)

    @commands.hybrid_command(aliases=["nukech"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @app_commands.describe(channel="Channel to nuke.")
    async def nukechannel(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Deletes and recreates a channel to clear all messages."""
        channel = channel or ctx.channel
        try:
            new_channel = await channel.clone(reason="Nuked by command")
            await new_channel.edit(position=channel.position)
            await channel.delete(reason="Nuked by command")
            await new_channel.send("💥 This channel has been nuked!")
            await self.log_action(ctx.guild, "Channel Nuked", ctx.author, new_channel)
        except discord.Forbidden:
            await ctx.send("I don't have permission to nuke this channel.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel="Channel to set topic.", new_topic="Topic to set.")
    async def topic(self, ctx, channel: Optional[discord.TextChannel] = None, *, new_topic: str = None):
        """Sets a channel's topic."""
        channel = channel or ctx.channel
        if not new_topic:
            await ctx.send("Please provide a topic.", ephemeral=True)
            return
        try:
            await channel.edit(topic=new_topic)
            await ctx.send(f"Updated topic for {channel.mention} to: {new_topic}")
            await self.log_action(ctx.guild, "Topic Changed", ctx.author, channel, f"New topic: {new_topic}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to edit this channel's topic.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(move_members=True)
    @app_commands.describe(member="User to deafen.")
    async def deafen(self, ctx, member: discord.Member):
        """Deafens a member in a voice channel."""
        if not member.voice:
            await ctx.send(f"{member.mention} is not in a voice channel.", ephemeral=True)
            return
        if member.voice.deaf:
            await ctx.send(f"{member.mention} is already deafened.", ephemeral=True)
            return
        try:
            await member.edit(deafen=True)
            await ctx.send(f"Deafened **{member.mention}**.")
            await self.log_action(ctx.guild, "Deafen", ctx.author, member)
        except discord.Forbidden:
            await ctx.send("I don't have permission to deafen this member.", ephemeral=True)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(move_members=True)
    @app_commands.describe(member="User to undeafen.")
    async def undeafen(self, ctx, member: discord.Member):
        """Undeafens a member in a voice channel."""
        if not member.voice:
            await ctx.send(f"{member.mention} is not in a voice channel.", ephemeral=True)
            return
        if not member.voice.deaf:
            await ctx.send(f"{member.mention} is not deafened.", ephemeral=True)
            return
        try:
            await member.edit(deafen=False)
            await ctx.send(f"Undeafened **{member.mention}**.")
            await self.log_action(ctx.guild, "Undeafen", ctx.author, member)
        except discord.Forbidden:
            await ctx.send("I don't have permission to undeafen this member.", ephemeral=True)




    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(role="The role you want to check.")
    async def dump(self, ctx, *, role: discord.Role):
        """Check all members in the specified role."""
        members = role.members
        member_list = []
        for member in members:
            member_list.append(f"{member.display_name} ({member.id})")
        member_str = "\n".join(member_list)
        embed = discord.Embed(title=f"Members in {role.name}", description=member_str, color=0x2F3136)
        await ctx.send(embed=embed)


    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_permissions=True)
    @app_commands.describe(member="The user you want to check permissions of.")
    async def perms(self, ctx, member: discord.Member = None):
        """Fetch a user's permissions'"""
        member = member or ctx.author
        allowed, denied = [], []

        for name, value in member.guild_permissions:
            if value:
                allowed.append(name.replace('_', ' ').title())
            else:
                denied.append(name.replace('_', ' ').title())

        embed = discord.Embed(title=f"Permissions for {member}", color=discord.Color.dark_embed())
        embed.add_field(name="Allowed", value="\n".join(allowed))
        embed.add_field(name="Denied", value="\n".join(denied))

        await ctx.send(embed=embed)




    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def banlist(self, ctx):
        """Displays the server's ban list."""
        banned_users = []
        async with ctx.typing():
            async for ban_entry in ctx.guild.bans():
                banned_users.append(ban_entry.user)
        if len(banned_users) == 0:
            await ctx.send("There are no banned users in this server.")
        else:
            banned_users_list = "\n".join([f"{user.name}#{user.discriminator} ({user.id})" for user in banned_users])
            embed = discord.Embed(title="Banned Users", description=banned_users_list, timestamp=ctx.message.created_at)
            await ctx.send(embed=embed)


    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def rolelist(self, ctx):
        """Displays the server's roles"""
        roles = ctx.guild.roles
        role_list = ""
        counter = 1
        for role in roles:
            role_list += f"`{counter}` - {role.mention}\n"
            counter += 1
        embed = discord.Embed(title=f"Roles in {ctx.guild.name}", description=role_list, color=discord.Color.dark_embed())
        await ctx.send(embed=embed)


    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def listchannel(self, ctx):
        """List the channels of the current server"""
        counter = 1
        text_channels = []
        voice_channels = []
        category_channels = []

        channels = ctx.guild.channels
        for channel in channels:
            if isinstance(channel, discord.TextChannel):
                text_channels.append(f"`{counter}` - {channel.mention}")
                counter += 1
            elif isinstance(channel, discord.VoiceChannel):
                voice_channels.append(f"`{counter}` - {channel.mention}")
                counter += 1
            elif isinstance(channel, discord.CategoryChannel):
                category_channels.append(f"`{counter}` - {channel.name}")
                counter += 1

        embeds = []

        if text_channels:
            text_channels_str = "\n".join(text_channels)
            if len(text_channels_str) > 1009:
                embed = discord.Embed(title=f"Text Channels in {ctx.guild.name}", color=discord.Color.dark_embed())
                while len(text_channels_str) > 0:
                    embed.add_field(name="Text Channels", value=text_channels_str[:1009], inline=False)
                    text_channels_str = text_channels_str[1009:]
                    embeds.append(embed)
                    embed = discord.Embed()
            else:
                embed = discord.Embed(title=f"Text Channels in {ctx.guild.name}", color=discord.Color.dark_embed())
                embed.add_field(name="Text Channels", value=text_channels_str, inline=False)
                embeds.append(embed)

        if voice_channels:
            voice_channels_str = "\n".join(voice_channels)
            if len(voice_channels_str) > 1009:
                embed = discord.Embed(title=f"Voice Channels in {ctx.guild.name}", color=discord.Color.dark_embed())
                while len(voice_channels_str) > 0:
                    embed.add_field(name="Voice Channels", value=voice_channels_str[:1009], inline=False)
                    voice_channels_str = voice_channels_str[1009:]
                    embeds.append(embed)
                    embed = discord.Embed()
            else:
                embed = discord.Embed(title=f"Voice Channels in {ctx.guild.name}", color=discord.Color.dark_embed())
                embed.add_field(name="Voice Channels", value=voice_channels_str, inline=False)
                embeds.append(embed)

        if category_channels:
            category_channels_str = "\n".join(category_channels)
            if len(category_channels_str) > 1009:
                embed = discord.Embed(title=f"Categories in {ctx.guild.name}", color=discord.Color.dark_embed())
                while len(category_channels_str) > 0:
                    embed.add_field(name="Categories", value=category_channels_str[:1009], inline=False)
                    category_channels_str = category_channels_str[1009:]
                    embeds.append(embed)
                    embed = discord.Embed()
            else:
                embed = discord.Embed(title=f"Categories in {ctx.guild.name}", color=discord.Color.dark_embed())
                embed.add_field(name="Categories", value=category_channels_str, inline=False)
                embeds.append(embed)

        if len(embeds) == 0:
            embed = discord.Embed(title=f"Channels in {ctx.guild.name}", color=discord.Color.dark_embed())
            if text_channels:
                embed.add_field(name="Text Channels", value="\n".join(text_channels), inline=False)
            if voice_channels:
                embed.add_field(name="Voice Channels", value="\n".join(voice_channels), inline=False)
            if category_channels:
                embed.add_field(name="Categories", value="\n".join(category_channels), inline=False)
            embeds.append(embed)

        for embed in embeds:
            await ctx.send(embed=embed)









async def setup(bot):
    await bot.add_cog(Moderation(bot))