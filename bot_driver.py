import discord
from discord.ext import commands
import os

client = commands.Bot(command_prefix = "?")

@client.event
async def on_ready():
    print("meh is alive and everything is pretty meh")

@client.command()
async def purge(ctx, arg = 0):
    del_num = int(arg)
    if del_num == 0:
        msg_count = 0
        async for msg in ctx.channel.history(limit=None):
            msg_count += 1
        await ctx.channel.purge(limit = msg_count)
    else:
        await ctx.channel.purge(limit = del_num)
    

@purge.error
async def purge_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.BadArgument):
        await ctx.send("Message format: ``?purge [number]`` or ``?purge``")


for file in os.listdir('./modules'):
    if file.endswith('.py'):
        client.load_extension(f'modules.{file[:-3]}')

client.run('NzI1MDMyNTA5ODg4NTI4NDA0.XvI1eA.9Ljt9Y6SuJNpY9e0kb9q-n4Y6-U')