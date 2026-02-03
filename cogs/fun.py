# cogs/fun.py
import discord
import random
import requests
from discord.ext import commands
from discord import app_commands
from main import get_guild_prefixes, update_prefixes_in_database, default_prefixes

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.compliments = [
            "You have a great sense of humor!",
            "Your kindness is contagious.",
            "You have a great smile.",
            "You have a beautiful soul.",
            "You always make people feel included.",
            "You're a great listener.",
            "You have a great work ethic.",
            "You're a fantastic friend.",
            "You always know how to brighten someone's day.",
            "You're an inspiration to those around you."
        ]

    @commands.hybrid_command()
    @app_commands.describe(sides="Number of sides")
    async def roll(self, ctx, sides: int):
        """Rolls a dice with the specified number of sides."""
        roll_result = random.randint(1, sides)
        embed = discord.Embed(
            description=f"**{ctx.author.name}** rolls **{roll_result}** (1-{sides})",
            color=discord.Color(0x83d09c)
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='8ball', aliases=['8b'])
    @app_commands.describe(question="The question you want to ask")
    async def _8ball(self, ctx, *, question=None):
        """Ask the magik 8ball a question"""
        if not question:
            await ctx.send('Please ask a question!', ephemeral=True)
            return
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.", "Yes – definitely.",
            "You may rely on it.", "As I see it, yes.", "Most likely.", "Outlook good.",
            "Yes.", "Signs point to yes.", "Reply hazy, try again.", "Ask again later.",
            "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "Outlook not so good.", "My sources say no.",
            "Very doubtful.", "My reply is no."
        ]
        embed = discord.Embed(
            title="Magik 8ball",
            description=f"**{ctx.author.mention} asked:**\n{question}\n**8ball says:**\n {random.choice(responses)}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=['cf'])
    async def coinflip(self, ctx):
        """Flips a coin"""
        await ctx.send(random.choice(['Heads!', 'Tails!']))

    @commands.hybrid_command()
    async def choose(self, ctx, *, option1: str, option2: str, option3: str = None, option4: str = None, option5: str = None):
        """Choose between multiple options"""
        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)
        if option5:
            options.append(option5)
        if len(options) < 2:
            await ctx.send("Please provide at least two options.", ephemeral=True)
            return
        if len(options) > 5:
            await ctx.send("Please provide up to five options.", ephemeral=True)
            return
        chosen_option = random.choice(options)
        await ctx.send(f"I choose: {chosen_option}")

    @commands.hybrid_command()
    @app_commands.choices(
        choice=[
            app_commands.Choice(name="Rock", value="rock"),
            app_commands.Choice(name="Paper", value="paper"),
            app_commands.Choice(name="Scissors", value="scissors")
        ]
    )
    @app_commands.describe(choice="Your choice. (rock, paper or scissors)")
    async def rps(self, ctx, choice: str):
        """Play a game of rock-paper-scissors with the bot."""
        choices = ["rock", "paper", "scissors"]
        choice = choice.lower()
        if choice not in choices:
            await ctx.send("Invalid choice! Please choose either rock, paper, or scissors.", ephemeral=True)
            return
        bot_choice = random.choice(choices)
        if choice == bot_choice:
            result = "It's a tie!"
            embed_color = discord.Color.blue()
        elif (
            (choice == "rock" and bot_choice == "scissors") or
            (choice == "paper" and bot_choice == "rock") or
            (choice == "scissors" and bot_choice == "paper")
        ):
            result = "You win!"
            embed_color = discord.Color.green()
        else:
            result = "You lose!"
            embed_color = discord.Color.red()
        response = {
            "rock": {
                "rock": f"Rock vs. rock?! **That's a tie!**",
                "paper": f"Paper covers rock. **{result}**",
                "scissors": f"Rock crushes scissors. **{result}**",
            },
            "paper": {
                "rock": f"Paper covers rock. **{result}**",
                "paper": f"Paper vs. paper?! **That's a tie!**",
                "scissors": f"Scissors cut paper! **{result}**",
            },
            "scissors": {
                "rock": f"Rock crushes scissors. **{result}**",
                "paper": f"Scissors cut paper! **{result}**",
                "scissors": f"Scissors vs. scissors?! **That's a tie!**",
            },
        }
        embed = discord.Embed(
            title="",
            description=response[choice][bot_choice],
            color=embed_color
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.guild_only()
    @app_commands.describe(member="The person you want to compliment.")
    async def compliment(self, ctx, member: discord.Member = None):
        """Compliments a user"""
        member = member or ctx.author
        compliment = random.choice(self.compliments)
        await ctx.send(f"{member.mention}, {compliment}")

    @commands.hybrid_command()
    async def dadjoke(self, ctx):
        """Get a random Dadjoke"""
        headers = {"Accept": "text/plain"}
        response = requests.get("https://icanhazdadjoke.com/", headers=headers)
        joke = response.text
        await ctx.send(joke)

async def setup(bot):
    await bot.add_cog(Fun(bot))