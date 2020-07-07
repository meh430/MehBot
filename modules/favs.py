import requests
import os
import discord
from discord.ext import commands
from pymongo import MongoClient
from modules.mal_rest.mal_helper import command_info
from modules.mal_rest.anime import Anime


class Favs(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.color = 0xFF99CC
        self.mongo = MongoClient(
            f"mongodb+srv://meh4life321:{str(os.environ['MONGO_PASS'])}@mehbot-bkb9k.mongodb.net/mehbot?retryWrites=true&w=majority")
        self.db = self.mongo.mehbot
        self.collection = self.db.favs

    @commands.command(aliases=['showfav'], brief='Display all your favorite shows')
    async def favs(self, ctx):
        if self.collection.count_documents({'_id': str(ctx.author)}) == 1:
            fav_doc = self.collection.find_one({'_id': str(ctx.author)})
            shows = sorted(fav_doc['favs'], key=lambda x: x['rank'])
            if not shows:
                return await ctx.send(f'Sorry {ctx.author}, you probably removed all the shows you had on your list. You can add more by using the command ``.addf [show id]``. To find the show id, use the ``.anime [name of show]`` command')

            fav_embed = discord.Embed(
                title=f"{ctx.author}'s Favorites", color=self.color)
            for i in range(0, len(shows)):
                show = shows[i]
                title = f"{i+1}) {show['title']}"
                show_id = show['mal_id']
                score = show['score']
                rank = show['rank']
                members = show['members']
                mal_url = show['url']
                body = f"Anime Id: {show_id}\nRank: {rank}\nScore: {score}\nMembers: {members}\nUrl: {mal_url}"
                fav_embed.add_field(name=title, value=body, inline=False)
            fav_embed.set_image(url=shows[0]['image_url'])
            await ctx.send(embed=fav_embed)
        else:
            await ctx.send(f'Sorry {ctx.author}, you have not added any favorite shows to your list. You can do so by using the command ``.addf [show id]``. To find the show id, use the ``.anime [name of show]`` command')

    @commands.command(aliases=['fav', 'addfav'], brief='Add a show to your favorites')
    async def addf(self, ctx, *, id: int):
        endpoint = 'https://api.jikan.moe/v3/anime/' + str(id)
        response = requests.get(url=endpoint, headers={
                                'User-agent': 'meh bot 1.0'}).json()
        if 'title' not in response:
            await ctx.send(f'``{id}`` not found')
            return

        anime = Anime(id=id, all_data=response)
        show = {
            'mal_id': id,
            'title': anime.title,
            'score': anime.rating,
            'rank': anime.rank,
            'members': anime.members,
            'url': anime.mal_url,
            'image_url': anime.image_url
        }

        if self.collection.count_documents({'_id': str(ctx.author)}) == 1:
            auth_entry = self.collection.find_one({'_id': str(ctx.author)})
            fav_shows = auth_entry['favs']
            if len(fav_shows) < 10:
                for s in fav_shows:
                    if id == s['mal_id']:
                        return await ctx.send("Looks like you've already added this show")

                fav_shows.append(show)
                self.collection.update_one({'_id': str(ctx.author)}, {
                                           '$set': {'favs': fav_shows}})
                await ctx.send(f'Added ``{anime.title}`` to your favorites')
            else:
                await ctx.send('Sorry, your list has reached the limit of 10 shows')
        else:
            new_entry = {
                '_id': str(ctx.author),
                'favs': [show]
            }
            await ctx.send(f'Added ``{anime.title}`` to your favorites')
            self.collection.insert_one(new_entry)

    @addf.error
    async def addf_error(self, ctx, error):
        aliases = ['fav', 'addfav']
        usages = ['.addf [anime id]', 'Anime id is a number']
        desc = 'Adds the specified show to your favorites list'
        await ctx.send(embed=command_info('addf', desc, aliases, usages))

    @commands.command(brief='Delete your favorites list')
    async def delfav(self, ctx):
        self.collection.delete_one({'_id': str(ctx.author)})
        await ctx.send('Deleted your list')

    @commands.command(brief='Remove a show from your list')
    async def rma(self, ctx, *, id: int):
        if self.collection.count_documents({'_id': str(ctx.author)}) == 1:
            auth_entry = self.collection.find_one({'_id': str(ctx.author)})
            fav_shows = auth_entry['favs']
            rm_index = None
            for i in range(0, len(fav_shows)):
                if fav_shows[i]['mal_id'] == id:
                    rm_index = i
                    break

            if rm_index:
                fav_shows.pop(i)
            else:
                return await ctx.send('You do not have that show in your list')

            self.collection.update_one({'_id': str(ctx.author)}, {
                                       '$set': {'favs': fav_shows}})
            await ctx.send(f'Removed {id} from your list')
        else:
            await ctx.send(f'Sorry {ctx.author}, you do not have a favorites list')

    @rma.error
    async def rma_error(self, ctx, error):
        aliases = ['removea', 'rmfav']
        usages = ['.rma [anime id]', '\nAnime id is a number']
        desc = 'Removes the specified show from your favorites list'
        await ctx.send(embed=command_info('addf', desc, aliases, usages))


def setup(client):
    client.add_cog(Favs(client))
