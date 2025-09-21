from nextcord.ext import commands
import nextcord
import os
from config import TOKEN

intents = nextcord.Intents.default()
intents.message_content = True
client = nextcord.Client(intents=intents)

bot = commands.Bot(command_prefix='oni!', intents=intents)
bot.remove_command("help")

@bot.event
async def on_ready():
    print(f'Бот: {bot.user}\nID: {bot.user.id}')

for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")

@bot.command()
async def servers(ctx):
    servers = list(bot.guilds)
    await ctx.send(f"Connected on {str(len(servers))} servers:")
    await ctx.send('\n'.join(server.name for server in servers))

bot.run(TOKEN)