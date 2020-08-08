import asyncio
import youtube_dl
import os
import discord
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

ydl_ops_dl = {
    'outtmpl': '%(title)s.%(ext)s',
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]
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

        file = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(file, **ffmpeg_ops), data=data)


class Youtube(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.music_stack = []
        self.delete_temp_media.start()
        self.color = 0xFF0000

    @commands.command(aliases=['jn', 'connect'], brief='Connect bot to a vc',
                      description='Connect the bot to a voice channel')
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        if ctx.voice_client:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @join.error
    async def join_error(self, ctx, error):
        voice_channels = [
            ch.name for ch in ctx.message.guild.channels if ch.type == discord.ChannelType.voice]
        vc_str = ', '.join(voice_channels)
        aliases = ['connect', 'jn']
        usages = ['.join [voice channel]\n', f'Voice Channels: {vc_str}']
        desc = 'Connect the bot to a voice channel'
        error_embed = command_info('join', desc, aliases, usages)
        return await ctx.send(embed=error_embed)

    @commands.command(aliases=['stream', 'music', 'yt'], brief='Plays specified music',
                      description='Play music from YouTube in a connected voice channel')
    async def play(self, ctx, *, url=''):
        aliases = ['stream', 'music', 'yt']
        usages = ['.play [video/music url]\n', '.play [query]']
        desc = 'Play music from YouTube in a connected voice channel'
        error_embed = command_info('play', desc, aliases, usages)
        if not url:
            return await ctx.send(embed=error_embed)

        async with ctx.typing():
            if ctx.voice_client.is_playing():
                player = await YTDLSource.from_url(url, loop=self.client.loop, stream=False)
                self.music_stack.append(player)
                await ctx.send(f'Added ``{player.title}`` to music stack')
            else:
                player = await YTDLSource.from_url(url, loop=self.client.loop, stream=False)
                ctx.voice_client.play(player, after=lambda e: print(
                    'Player error: %s' % e) if e else self.play_next(ctx))
                await ctx.send(f'Playing ``{player.title}``')

    @play.error
    async def play_error(self, ctx, error):
        await ctx.send(f'Error finding song: {error}')

    @commands.command(aliases=['vol'], brief='Change volume of the music player', description='Change volume of the music player')
    async def volume(self, ctx, volume: int):
        if volume < 0 or volume > 100:
            raise commands.CommandError(message='Volume out of bounds')

        if not ctx.voice_client:
            return await ctx.send('Not connected to a voice channel.')

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f'Changed volume to ``{volume}``%')

    @volume.error
    async def volume_error(self, ctx, error):
        aliases = ['vol']
        usages = ['.volume [integer between 0 and 100]']
        desc = 'Adjust the volume of music being played in voice channel'
        error_embed = command_info('volume', desc, aliases, usages)
        await ctx.send(embed=error_embed)

    @commands.command(aliases=['disconnect'], brief='Stops the music player',
                      description='Stops the music player and disconnects from vc')
    async def stop(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()

        await ctx.send('Disconnected from vc.')

    @commands.command(aliases=['ps'], brief='Pauses music', description='Pauses the music being played in a voice channel')
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()

    @commands.command(aliases=['playlist'], brief='Display music stack', description='Display music left in the stack')
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

    @commands.command(aliases=['skip'], brief='Skips to the top song on the stack',
                      description='Skips to the top song on the stack')
    async def next(self, ctx):
        if self.music_stack and ctx.voice_client:
            ctx.voice_client.stop()
            next_song = self.music_stack.pop()
            await ctx.send(f'Playing ``{next_song.title}``')
            ctx.voice_client.play(next_song, after=lambda e: print(
                'Player error: %s' % e) if e else self.play_next(ctx))
        else:
            await ctx.send('No music in stack')

    @commands.command(aliases=['res'], brief='Resumes song if it was paused', description='Resumes song if it was paused')
    async def resume(self, ctx):
        if ctx.voice_client and not ctx.voice_client.is_playing():
            ctx.voice_client.resume()

    @commands.command(aliases=['dl'], brief='Makes music from YouTube downloadable', description='Finds specified video on YouTube and makes it downloadable in mp3 format')
    async def download(self, ctx, *, query=''):
        info = {}
        if not query:
            aliases = ['dl']
            usages = ['.download [query/url]']
            desc = 'Download specified youtube video'
            error_embed = command_info('download', desc, aliases, usages)
            return await ctx.send(embed=error_embed)

        async with ctx.typing():
            with youtube_dl.YoutubeDL(ydl_ops_dl) as ydl:
                info = ydl.extract_info(query, download=True)
                # in case url wasn't given, just get first result
                if 'entries' in info:
                    info = info['entries'][0]
                ydl.download([info['webpage_url']])

            # needs more testing, some characters are converted when downloading
            name = info['title'].replace(
                '/', '_').replace('|', '_').replace(':', ' -')
            print('fname: ' + name)
            print(os.listdir('.'))
            if os.path.exists('./' + name + '.mp3'):
                await ctx.send(f"Downloaded ``{name}``\n{info['webpage_url']}")
                with open(name + '.mp3', 'rb') as file:
                    await ctx.send(file=discord.File(file, name + '.mp3'))
                return

        await ctx.send('Could not download...')

    @download.error
    async def download_error(self, ctx, error):
        await ctx.send('Error finding song')
        await ctx.send(f'{error}')

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if not ctx.voice_client:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send('You are not connected to a voice channel.')
                raise commands.CommandError(
                    'Author not connected to a voice channel.')

    @tasks.loop(minutes=10.0)
    async def delete_temp_media(self):
        for file in os.listdir('.'):
            print('other: ' + file)
            if file.endswith('.webm') or file.endswith('.mp3') or file.endswith('.m4a'):
                print(file)
                try:
                    os.remove(file)
                except OSError as e:
                    print(e)

    def play_next(self, ctx):
        if len(self.music_stack) >= 1:
            next_song = self.music_stack.pop()
            if ctx.voice_client:
                asyncio.run_coroutine_threadsafe(
                    ctx.send(f'Playing ``{next_song.title}``'), self.client.loop)
                ctx.voice_client.play(next_song, after=lambda e: print(
                    'Player error: %s' % e) if e else self.play_next(ctx))

            else:
                asyncio.run_coroutine_threadsafe(
                    ctx.send('Not connected to vc'), self.client.loop)

        else:
            asyncio.sleep(90)
            if not ctx.voice_client.is_playing():
                asyncio.run_coroutine_threadsafe(
                    ctx.send("No more songs in queue."), self.client.loop)
                asyncio.run_coroutine_threadsafe(
                    ctx.voice_client.disconnect(), self.client.loop)


def setup(client):
    client.add_cog(Youtube(client))
