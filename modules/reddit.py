import discord
from discord.ext import commands, tasks
import requests
from random import randint
from datetime import datetime
import os
import json
# reddit notify? weather? dict, thes? qotd? youtube download?
FEED = 'feed_settings.json'
LAST = 'last_post.json'
class Reddit(commands.Cog):
    post_sort = ['new', 'hot', 'top']
    top_sort = ['all', 'year', 'month', 'week', 'day', 'hour']
    
    def __init__(self, client):
        self.client = client
        self.feed_settings = {}
        if not os.path.exists('./' + FEED):
            self.feed_settings['sub'] = 'dankmemes'
            self.feed_settings['active'] = False
            with open(FEED, 'w') as file:
                json.dump(self.feed_settings, file)
        else:
            with open(FEED, 'r') as file:
                self.feed_settings = json.load(file)

        self.last_post = {}
        if not os.path.exists('./' + LAST):
            self.last_post['title'] = ''
            with open(LAST, 'w') as file:
                json.dump(self.last_post, file)
        else:
            with open(LAST, 'r') as file:
                self.last_post = json.load(file)

        if self.feed_settings['active']:
            self.update_feed.start()

        print(self.feed_settings)
        print(self.last_post)

    @commands.command(aliases=['reddit'])
    async def r(self, ctx, *, sub=''):
        if (sub == ''):
            await ctx.send("Message format: ``?r [subreddit]``")
            return
        sub = sub.replace(' ', '')
        sort = Reddit.post_sort[randint(0, len(Reddit.post_sort)-1)]
        endpoint = 'https://www.reddit.com/r/' + sub + '/' + sort + '/.json'
        if sort == 'top':
            endpoint += ('?t=' + Reddit.top_sort[randint(0, len(Reddit.top_sort) - 1)])

        res = requests.get(url=endpoint, headers={
                           'User-agent': 'your bot 0.1'}).json()
        if 'data' not in res:
            self.find_alt_reddits(ctx, sub)
            return
        else:
            res = res['data']['children']

        post = res[randint(0, len(res)-1)]
        post_data = post['data']
        post_embed = self.create_post_embed(post_data=post_data)
        await ctx.send(embed=post_embed)

    @commands.command()
    async def rstart(self, ctx, *, sub=""):
        sub = sub.replace(' ', '')
        if self.feed_settings['active']:
            await ctx.send('Feed is already active.')
            return

        success = False
        if sub != '':
            endpoint = 'https://www.reddit.com/r/' + sub + '/new/.json?limit=1'
            res = requests.get(url=endpoint, headers={
                               'User-agent': 'your bot 0.1'}).json()
            if 'data' not in res:
                self.find_alt_reddits(ctx, sub)
                success = False
            else:
                self.feed_settings['sub'] = sub
                success = True
        else:
            success = True
        self.feed_settings['active'] = success

        if success:
            await self.delete_all_messages(ctx)

        with open(FEED, 'w') as file:
            json.dump(self.feed_settings, file)

        self.update_feed.start()
        
    @commands.command()
    async def rend(self, ctx):
        self.update_feed.cancel()
        self.feed_settings['active'] = False
        with open(FEED, 'w') as file:
            json.dump(self.feed_settings, file)

        await self.delete_all_messages(ctx)
        await ctx.send('Feed stopped.')

    @tasks.loop(seconds=10.0)
    async def update_feed(self):
        print('feed update')
        print(self.feed_settings)
        print(self.last_post)
        # post request and find if the post is new/different
        endpoint = 'https://www.reddit.com/r/' + self.feed_settings['sub'] + '/new/.json?limit=1'
        new_post = requests.get(url=endpoint, headers={
                                'User-agent': 'your bot 0.1'}).json()['data']['children'][0]['data']
        #different post found
        if self.last_post['title'] != new_post['title']:
            self.last_post['title'] = new_post['title']
            post_embed = self.create_post_embed(post_data=new_post)
            await self.client.get_channel(726803865021972592).send(embed=post_embed)
            with open(LAST, 'w') as file:
                json.dump(self.last_post, file)

    async def delete_all_messages(self, ctx):
        msg_count = 0
        async for msg in ctx.channel.history(limit=None):
            msg_count += 1
        print("MESSAGE COUNT: " + str(msg_count))
        await ctx.channel.purge(limit = msg_count)

    def create_post_embed(self, post_data):
        reddit_embed = discord.Embed(title=post_data['title'])

        reddit_embed.add_field(
            name='Subreddit:', value=post_data['subreddit_name_prefixed'], inline=False)

        reddit_embed.add_field(
            name='Upvotes:', value=post_data['ups'], inline=True)

        post_date = datetime.utcfromtimestamp(
            int(post_data['created_utc'])).strftime('%Y-%m-%d %H:%M')
        reddit_embed.add_field(
            name='Posted On:', value=str(post_date), inline=True)

        permalink = 'https://www.reddit.com' + post_data['permalink']
        reddit_embed.add_field(name='Post Link', value=permalink, inline=False)
        
        if 'preview' in post_data:
            media_data = post_data['preview']['images'][0]
            is_gif = 'gif' in media_data['variants']
            link = 'https://thumbs.dreamstime.com/b/no-image-available-icon-photo-camera-flat-vector-illustration-132483141.jpg'
            if is_gif:
                link = media_data['variants']['gif']['source']['url'].replace(
                    'amp;', '')
            else:
                link = media_data['source']['url'].replace('amp;', '')
            reddit_embed.set_image(url=link)
        elif 'selftext' in post_data and post_data['selftext'] != '':
            reddit_embed.add_field(name='Body', value=str(
                post_data['selftext']), inline=False)

        if 'url' in post_data and post_data['url'] != '' and post_data['url'] != permalink:
            reddit_embed.add_field(name='Link', value=str(
                post_data['url']), inline=False)
        return reddit_embed
    
    async def find_alt_reddits(self, ctx, sub=""):
        # sub not found
        alt_endpoint = 'https://www.reddit.com/api/search_reddit_names/.json?query=' + sub
        other_reddits = requests.get(url=alt_endpoint, headers={
                                     'User-agent': 'your bot 0.1'}).json()
        if len(other_reddits['names']) == 0:
            await ctx.send(f'``{sub}`` not found.')
        else:
            await ctx.send(f'``{sub}`` not found. Were you looking for ``{other_reddits["names"]}``')


def setup(client):
    client.add_cog(Reddit(client))
