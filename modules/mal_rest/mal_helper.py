import requests
import discord
from modules.mal_rest.anime import Anime
# just funtions


def get_anime(query):
    args = {'q': query, 'page': 1}
    search_result = requests.get(url='https://api.jikan.moe/v3/search/anime', headers={
                                 'User-agent': 'meh bot 1.0'}, params=args).json()['results']
    limit = len(search_result) if len(search_result) < 5 else 5
    checked = 0
    animes = []
    for result in search_result:
        if checked >= limit:
            break
        curr_anime = Anime(result['mal_id'])
        print(result['mal_id'])
        if curr_anime.is_similar(query):
            return curr_anime
        else:
            animes.append(curr_anime.title)
            print(animes)
            checked += 1

    return animes


def get_top(type, sub_type=''):
    endpoint = 'https://api.jikan.moe/v3/top/' + type + '/1/' + sub_type
    top_list = requests.get(url=endpoint, headers={
                            'User-agent': 'meh bot 1.0'}).json()['top']
    ret = []
    limit = len(top_list) if len(top_list) < 10 else 10
    added = 0
    # all three use same basic schema in the api
    for item in top_list:
        if added >= limit:
            break
        data = {
            'title': item['title'],
            'image_url': item['image_url'], 'rank': item['rank'],
            'url': item['url'],
            'score': item['score'] if 'score' in item else 0,
            'members': item['members'] if 'members' in item else item['favorites']}
        ret.append(Anime(data=data))
        added += 1
    return ret


def season_info(year=2012, season='summer'):
    endpoint = 'https://api.jikan.moe/v3/season/' + str(year) + '/' + season
    animes = requests.get(url=endpoint, headers={
                          'User-agent': 'meh bot 1.0'}).json()['anime']
    limit = len(animes) if len(animes) < 5 else 5
    added = 0
    season_list = []
    for anime in animes:
        if added >= limit:
            break
        data = {
            'title': anime['title'], 'image_url': anime['image_url'], 'url': anime['url'],
            'score': anime['score'] if 'score' in anime else 0, 'members': anime['members']}
        season_list.append(Anime(data=data))
        added += 1
    return season_list


def command_info(command, desc, aliases, usages):
    info_embed = discord.Embed(title='Command: .' + command, color=0xff0000)
    info_embed.add_field(name='Description', value=desc, inline=False)
    al_formatted = ''
    for alias in aliases:
        al_formatted += '.' + alias + ', '
    al_formatted = al_formatted[:-2]
    info_embed.add_field(name='Aliases', value=al_formatted, inline=False)
    use_formatted = ''
    for usage in usages:
        use_formatted += usage
    info_embed.add_field(name='Usage', value=use_formatted, inline=False)
    return info_embed
