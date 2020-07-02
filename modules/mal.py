import discord
from discord.ext import commands
from modules.mal_rest.mal_helper import get_anime, get_top, season_info, command_info
from modules.mal_rest.anime import Anime


class Mal(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=['animu', 'ani'])
    async def anime(self, ctx, *, arg=''):
        if arg == '':
            aliases = ['animu', 'ani']
            usages = ['?anime [name of show]']
            desc = 'Display info on specified anime'
            await ctx.send(embed=command_info('anime', desc, aliases, usages))
            return

        async with ctx.typing():
            anime = get_anime(arg)
            if isinstance(anime, Anime):
                anime_embed = discord.Embed(title=anime.title)
                anime_embed.add_field(
                    name='MAL Link:', value=anime.mal_url, inline=False)
                anime_embed.add_field(
                    name='Episodes:', value=anime.ep_num, inline=True)
                anime_embed.add_field(
                    name='Score:', value=anime.rating, inline=True)
                anime_embed.add_field(
                    name='Rank:', value=anime.rank, inline=True)
                if anime.studio != '':
                    anime_embed.add_field(
                        name='Studio:', value=anime.studio, inline=True)
                anime_embed.add_field(name='Air Period:',
                                      value=anime.air_period, inline=True)
                genres = str(anime.genres)
                anime_embed.add_field(
                    name='Genres:', value=genres[1:len(genres)-1], inline=False)
                if len(anime.synopsis) > 1000:
                    anime.synopsis = anime.synopsis[:997]
                    anime.synopsis += '...'
                anime_embed.add_field(
                    name='Synopsis:', value=anime.synopsis, inline=True)
                anime_embed.set_image(url=anime.image_url)
                await ctx.send(embed=anime_embed)
            else:
                await ctx.send("``" + arg + "`` not found. Were you looking for " + str(anime))

    @commands.command(aliases=['top_mal', 'topmal'])
    async def top(self, ctx, type='', sub_type=''):
        valid_sub = ('all', 'airing', 'upcoming',
                     'tv', 'movie', 'ova', 'special')
        type = type.lower()
        sub_type = sub_type.lower()
        aliases = ['top_mal', 'topmal']
        usages = ['?top [type] [*optional* subtype]\n', "Types are 'anime', 'manga', and 'characters'\n",
                  "Note: subtype can oly be specified if the type is 'anime'\n", "Subtypes are 'all', 'airing', 'upcoming', 'tv', 'movie', 'ova', and 'special'"]
        desc = 'Display the top anime, manga, or characters on MAL'
        error_embed = command_info('top', desc, aliases, usages)
        emb_title = ''
        top_list = []
        people = ''
        if type == 'anime':
            if sub_type not in valid_sub:
                sub_type = ''
            emb_title = 'Top ' + sub_type + ' anime'
            async with ctx.typing():
                top_list = get_top('anime', sub_type)
            people = 'Members'
        elif type == 'manga':
            emb_title = 'Top manga'
            async with ctx.typing():
                top_list = get_top('manga')
            people = 'Members'
        elif type == 'character' or type == 'characters' or type == 'char':
            emb_title = 'Top character'
            async with ctx.typing():
                top_list = get_top('characters')
            people = 'Favs'
        else:
            await ctx.send(embed=error_embed)

        top_embed = discord.Embed(title=emb_title)
        top_embed.set_image(url=top_list[0].image_url)

        for item in top_list:
            print(item.title)
            top_embed.add_field(name=f'{item.rank}) {item.title}',
                                value=f'Score: {item.rating}\n{people}: {item.members}\nurl: {item.mal_url}', inline=False)

        await ctx.send(embed=top_embed)

    @commands.command(aliases=['ssn', 'sn'])
    async def season(self, ctx, year=0, season=''):
        seasonal_anime = []
        seasons = ['winter', 'spring', 'summer', 'fall']
        aliases = ['ssn', 'sn']
        usages = ['?season [year] [season]\n',
                  "Seasons are 'winter', 'spring', 'summer', and 'fall'"]
        desc = 'Display the most popular anime for a specified season'
        error_embed = command_info('season', desc, aliases, usages)
        if year == 0 or season == '' or season not in seasons:
            await ctx.send(embed=error_embed)
            return
        else:
            async with ctx.typing():
                seasonal_anime = season_info(year, season)
            if len(seasonal_anime) == 0:
                await ctx.send('No anime found')
            else:
                season_embed = discord.Embed(
                    title=f'Season of {season} {year}')
                season_embed.set_image(url=seasonal_anime[0].image_url)
                num = 1
                for anime in seasonal_anime:
                    season_embed.add_field(
                        name=f'{num}) {anime.title}', value=f'Score: {anime.rating}\nMembers: {anime.members}\nurl: {anime.mal_url}', inline=False)
                    num += 1
                await ctx.send(embed=season_embed)


def setup(client):
    client.add_cog(Mal(client))
