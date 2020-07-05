import os
import discord
from discord.ext import commands
from modules.mal_rest.mal_helper import command_info
client = commands.Bot(command_prefix=".")


@client.event
async def on_ready():
    print('meh is alive and everything is pretty meh')


@client.command(aliases=['delete', 'clear'])
async def purge(ctx, arg=0):
    del_num = int(arg)
    if not del_num:
        msg_count = 0
        async for msg in ctx.channel.history(limit=None):
            msg_count += 1
        await ctx.channel.purge(limit=msg_count)
    else:
        await ctx.channel.purge(limit=del_num)


@purge.error
async def purge_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.BadArgument):
        aliases = ['delete', 'clear']
        usages = ['.purge\n', '.purge [number of messages]']
        desc = 'Delete all messages in a channel or specify the number of messages to be deleted'
        await ctx.send(embed=command_info('purge', desc, aliases, usages))


for file in os.listdir('./modules'):
    if file.endswith('.py'):
        print(file)
        client.load_extension(f'modules.{file[:-3]}')

client.run(str(os.environ['BOT_ID']))
