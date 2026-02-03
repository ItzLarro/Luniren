# cogs/image.py
import discord
import requests
from discord.ext import commands
from discord import app_commands
from main import get_guild_prefixes, update_prefixes_in_database, default_prefixes

class Image(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def cat(self, ctx):
        """Fetches a random image of a cat"""
        response = requests.get('https://api.thecatapi.com/v1/images/search')
        data = response.json()
        if data:
            image_url = data[0]['url']
            embed = discord.Embed(title='Cat', color=discord.Color.random(), timestamp=ctx.message.created_at)
            embed.set_image(url=image_url)
            await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def dog(self, ctx):
        """Fetches a random image of a dog"""
        response = requests.get('https://dog.ceo/api/breeds/image/random')
        data = response.json()
        if data['status'] == 'success':
            image_url = data['message']
            embed = discord.Embed(title='Dog', color=discord.Color.random(), timestamp=ctx.message.created_at)
            embed.set_image(url=image_url)
            await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=['av'])
    @app_commands.describe(member="The user you want to get the avatar of.")
    async def avatar(self, ctx, member: discord.Member | discord.User = None):
        """Displays a user's avatar"""
        member = member or ctx.author
        if isinstance(member, discord.User):
            user = await self.bot.fetch_user(member.id)
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        else:
            user = member
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        if not user.avatar:  
            return await ctx.send("The user does not have an avatar.", ephemeral=True)
        embed = discord.Embed(timestamp=ctx.message.created_at)
        embed.set_image(url=avatar_url)
        embed.set_author(name=user.name, icon_url=user.avatar.url)
        embed.set_footer(text=f"- {user.name if user == ctx.author else ctx.author.name}",
        icon_url=avatar_url if user == ctx.author else (ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url))
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='avatarserver', aliases=['avs'])
    @commands.guild_only()
    @app_commands.describe(server_id="The id of the server you want to get the avatar of.")
    async def server_avatar(self, ctx, server_id: str = None):
        """Displays the avatar of a specific server."""
        if server_id:
            try:
                guild = await self.bot.fetch_guild(int(server_id))
            except discord.errors.NotFound:
                await ctx.send("The provided server ID is invalid or I'm not in that server.", ephemeral=True)
                return
        else:
            guild = ctx.guild
        avatar_url = guild.icon.url if guild.icon else None
        if not avatar_url:
            await ctx.send(f"The server {guild.name} does not have an avatar.", ephemeral=True)
            return
        embed = discord.Embed(title="", timestamp=ctx.message.created_at)
        embed.set_author(name=guild.name, icon_url=guild.icon.url)
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"- {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @app_commands.describe(user="The user you want to get the banner of.")
    async def banner(self, ctx, user: discord.User):
        """Retrieves the banner of a user"""
        try:
            user = await self.bot.fetch_user(user.id)
        except discord.NotFound:
            return await ctx.send("User not found.", ephemeral=True)
        if user.banner is None:
            return await ctx.send("The user does not have a banner.", ephemeral=True)
        embed = discord.Embed(timestamp=ctx.message.created_at)
        embed.set_image(url=user.banner.url)
        embed.set_author(name=user.name, icon_url=user.avatar.url)
        embed.set_footer(text=f"- {user.name if user == ctx.author else ctx.author.name}",
        icon_url=ctx.avatar_url if user == ctx.author else (ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url))
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='bannerserver')
    @commands.guild_only()
    @app_commands.describe(server_id="The id of the server you want to get the banner of.")
    async def server_banner(self, ctx, server_id: str = None):
        """Displays the banner of a specific server."""
        if server_id:
            try:
                guild = await self.bot.fetch_guild(int(server_id))
            except discord.errors.NotFound:
                await ctx.send("The provided server ID is invalid or I'm not in that server.", ephemeral=True)
                return
        else:
            guild = ctx.guild
        banner_url = guild.banner.url if guild.banner else None
        if not banner_url:
            await ctx.send(f"The server {guild.name} does not have a banner.", ephemeral=True)
            return
        embed = discord.Embed(title="", timestamp=ctx.message.created_at)
        embed.set_author(name=guild.name, icon_url=guild.icon.url)
        embed.set_image(url=banner_url)
        embed.set_footer(text=f"- {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)




async def setup(bot):
    await bot.add_cog(Image(bot))