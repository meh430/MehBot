import asyncio
import youtube_dl
import discord
import os
from discord.ext import commands, tasks
from modules.mal_rest.mal_helper import command_info

ytdl_ops = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_ops = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_ops)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.url = data.get('url')
        self.title = data.get('title')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        # get event loop and get list of videos from query
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]
        else:
            return 'F'

        file = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(file, **ffmpeg_ops), data=data)


class Youtube(commands.Cog):
    def __init__(self, client):
        self.client = client
        discord.opus.load_opus('opus')
        self.music_stack = []
        self.delete_temp_media.start()
        self.color = 0xff0000

    # join specified voice channel
    @commands.command(aliases=['jn', 'connect'])
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        if not channel:
            voice_channels = [
                ch.name for ch in ctx.message.guild.channels if ch.type == discord.ChannelType.voice]
            vc_str = str(voice_channels)[1:-1]
            aliases = ['connect', 'jn']
            usages = ['?join [voice channel]\n', f'Voice Channels: {vc_str}']
            desc = 'Connect MehBot to a voice channel'
            error_embed = command_info('join', desc, aliases, usages)
            await ctx.send(embed=error_embed)
            return

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command(aliases=['stream', 'music', 'yt'])
    async def play(self, ctx, *, url=''):
        aliases = ['stream', 'music', 'yt']
        usages = ['?play [video/music url]\n', '?play [query]']
        desc = 'Play music from YouTube in a connected voice channel'
        error_embed = command_info('play', desc, aliases, usages)
        if url == '':
            await ctx.send(embed=error_embed)
            return

        print(ctx.voice_client.is_playing())

        async with ctx.typing():
            if ctx.voice_client.is_playing():
                player = await YTDLSource.from_url(url, loop=self.client.loop, stream=False)
                self.music_stack.append(player)
                await ctx.send("Added ``{}`` to music stack".format(player.title))
            else:
                player = await YTDLSource.from_url(url, loop=self.client.loop, stream=False)
                ctx.voice_client.play(player, after=lambda e: print(
                    'Player error: %s' % e) if e else None)
                await ctx.send("Playing ``{}``".format(player.title))
        # states: Newly added song. Song playing, add to stack

    @play.error
    async def play_error(self, ctx, error):
        await ctx.send('Error finding song')
        await ctx.send(f'{error}')

    @commands.command()
    async def volume(self, ctx, volume: int):

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Changed volume to ``{}``%".format(volume))

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()

        await ctx.send('MehBot is not connected to vc.')

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()

    @commands.command(aliases=['playlist'])
    async def stack(self, ctx):
        if self.music_stack:
            stack_embed = discord.Embed(title='Music Stack', color=self.color)
            music = ''
            for i in range(len(self.music_stack) - 1, -1, -1):
                music += '- ' + \
                    self.music_stack[i].title + ('\n' if i != 0 else '')
            stack_embed.add_field(name='Stack:', value=music, inline=False)
            await ctx.send(embed=stack_embed)
        else:
            await ctx.send('No music in stack')

    @commands.command(aliases=['skip'])
    async def next(self, ctx):
        if self.music_stack and ctx.voice_client:
            ctx.voice_client.stop()
            next_song = self.music_stack.pop()
            await ctx.send("Playing ``{}``".format(next_song.title))
            ctx.voice_client.play(next_song, after=lambda e: print(
                'Player error: %s' % e) if e else None)
        else:
            await ctx.send('No music in stack')

    @commands.command(aliases=['res'])
    async def resume(self, ctx):
        if ctx.voice_client and not ctx.voice_client.is_playing():
            ctx.voice_client.resume()

    @commands.command(aliases=['rm'])
    async def remove(self, ctx):
        if self.music_stack:
            removed = self.music_stack.pop()
            await ctx.send("``{}`` was removed".format(removed.title))
        else:
            await ctx.send('No music in stack')

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError(
                    "Author not connected to a voice channel.")

    @tasks.loop(minutes=10.0)
    async def delete_temp_media(self):
        for file in os.listdir('.'):
            print('other: ' + file)
            if file.endswith('.webm') or file.endswith('.mp3'):
                print(file)
                try:
                    os.remove(file)
                except OSError as e:
                    print(e)


def setup(client):
    client.add_cog(Youtube(client))
