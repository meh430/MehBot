import requests
import discord
from discord.ext import commands
from modules.mal_rest.mal_helper import command_info


class Words(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.color = 0xC400FF

    @commands.command(aliases=['definition', 'def', 'dict'])
    async def define(self, ctx, *, query=''):
        if not query:
            aliases = ['definition', 'def', 'dict']
            usages = ['?define [word]']
            desc = 'Defines a given word'
            error_embed = command_info('define', desc, aliases, usages)
            await ctx.send(embed=error_embed)
            return
        endpoint = 'https://mashape-community-urban-dictionary.p.rapidapi.com/define'
        headers = {
            'x-rapidapi-host': 'mashape-community-urban-dictionary.p.rapidapi.com',
            'x-rapidapi-key': '2ce34e2faemsh8889ea266be5da0p154b57jsn9a241b94417e',
            'User-agent': 'meh bot 1.0'
        }
        definitions = requests.get(
            url=endpoint, headers=headers, params={'term': query}).json()

        print(definitions)
        if 'list' in definitions and definitions['list']:
            def_list = definitions['list']
            limit = len(def_list) if len(def_list) < 3 else 3
            added = 0
            def_embed = discord.Embed(
                title="Definitions found for '{}'".format(query), color=self.color)
            for definition in def_list:
                if added >= limit:
                    break

                curr_def = definition['definition']
                curr_def += '\n\nEXAMPLE: ' + definition['example']
                def_embed.add_field(name="Definition #{}".format(
                    added+1), value=curr_def, inline=False)
                added += 1

            def_embed.set_footer(text="Source: Urban Dictionary")
            await ctx.send(embed=def_embed)
        else:
            await ctx.send("No definitions foud for ``{}``".format(query))

    @commands.command(aliases=['synonym', 'syn'])
    async def thes(self, ctx, *, query=''):
        if not query:
            aliases = ['synonym', 'syn']
            usages = ['?thes [word]']
            desc = 'Finds synonym for a word'
            error_embed = command_info('thes', desc, aliases, usages)
            await ctx.send(embed=error_embed)
            return

        endpoint = "https://www.dictionaryapi.com/api/v3/references/thesaurus/json/{}?key=bf4cb80e-99a0-40a8-b352-4ced1d34cd77".format(
            query)

        response = requests.get(url=endpoint, headers={
                                'User-agent': 'meh bot 1.0'}).json()

        if response:
            response = response[0]['meta']['syns']
            synonyms = []
            thes_embed = discord.Embed(
                title='Synonyms:', color=self.color)
            for item in response:
                if type(item) is list:
                    thes_embed.add_field(name=query, value=str(item)[
                                         1:-1], inline=False)
                else:
                    synonyms.append(item)

            if synonyms:
                thes_embed.add_field(name=query, value=str(
                    synonyms)[1:-1], inline=False)
            await ctx.send(embed=thes_embed)
        else:
            await ctx.send("No synonyms found for ``{}``".format(query))

    @thes.error
    async def thes_error(self, ctx, error):
        await ctx.send('Something went wrong finding synonyms :(')

    @commands.command(aliases=['rhy'])
    async def rhyme(self, ctx, *, query):
        if not query:
            aliases = ['rhy']
            usages = ['?rhy [word]']
            desc = 'Finds words that rhyme with a specified word'
            error_embed = command_info('rhyme', desc, aliases, usages)
            await ctx.send(embed=error_embed)
            return

        endpoint = 'https://api.datamuse.com/words?rel_rhy=' + query
        rhymes = requests.get(url=endpoint, headers={
                              'User-agent': 'meh bot 1.0'}).json()

        if rhymes:
            limit = len(rhymes) if len(rhymes) < 15 else 15
            added = 0
            rhyme_display = []
            for rhyme in rhymes:
                if added >= limit:
                    break
                rhyme_display.append(rhyme['word'])
                added += 1
            rhyme_embed = discord.Embed(
                title="Words that rhyme with {}".format(query), color=self.color)
            print(rhyme_display)
            rhyme_embed.add_field(name='Rhymes', value=str(
                rhyme_display)[1:-1], inline=False)
            await ctx.send(embed=rhyme_embed)
        else:
            await ctx.send("No rhymes found for ``{}``".format(query))


def setup(client):
    client.add_cog(Words(client))
