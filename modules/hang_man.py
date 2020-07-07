import os
import json
import discord
from discord.ext import commands
from random import randint
from modules.mal_rest.mal_helper import command_info


class HangMan(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.state = 0
        self.target = ''
        self.word_state = []
        self.word_list = []
        self.guessed = []
        self.running = False
        print(os.listdir('.'))
        with open('./modules/hm/words.json', 'r') as file:
            self.word_list = json.load(file)['data']

    @commands.command(aliases=['starth', 'hstart', 'hm'], brief='Start a game of hang man')
    async def hangman(self, ctx):
        if self.running:
            return await ctx.send("Game is already running. Use ``.hstop`` to end the game")

        self.running = True
        self.target = self.word_list[randint(0, len(self.word_list)-1)]
        self.word_state = ['--'] * len(self.target)
        self.guessed = [False] * len(self.target)
        print(self.target + str(self.word_state))
        await self.h_embed(ctx)

    @commands.command(aliases=['stoph'], brief='Stop a game of hang man')
    async def hstop(self, ctx):
        self.reset()
        await ctx.send('Hang man stopped')

    @commands.command(aliases=['g'], brief='Allows player to guess a letter while playing hang man')
    async def guess(self, ctx, *, letter=''):
        if letter == '':
            aliases = ['g']
            usages = ['.guess [letter]']
            desc = 'Guess a letter for hang man'
            return await ctx.send(embed=command_info('guess', desc, aliases, usages))

        elif not self.running:
            return await ctx.send("Hangman is not being played right now. Use ``.hm`` to start a game")

        letter = letter[0:1].lower()
        indices = []
        for i in range(0, len(self.target)):
            if not self.guessed[i] and self.target[i] == letter:
                indices.append(i)
                self.guessed[i] = True

        if indices:
            for index in indices:
                self.word_state[index] = self.target[index]
        else:
            self.state += 1

        if self.target == ''.join(self.word_state):
            await ctx.send('Congrats, you guessed the word ``{}``'.format(self.target))
            self.reset()
            return
        await self.h_embed(ctx)

    async def h_embed(self, ctx):
        emb = discord.Embed(title='Hang Man', color=0x1F7A31)
        if self.state == 7:
            emb.add_field(name='You Lost!', value='  '.join(self.word_state) +
                          '\nActual Word: ' + self.target, inline=False)
        else:
            emb.add_field(
                name='Make a guess using ?guess [letter]', value='  '.join(self.word_state), inline=False)

        state_img = discord.File(
            './modules/hm/hm' + str(self.state) + '.png', filename='hm'+str(self.state)+'.png')
        emb.set_image(url='attachment://hm'+str(self.state)+'.png')
        await ctx.send(file=state_img, embed=emb)

        if self.state == 7:
            self.reset()

    def reset(self):
        self.running = False
        self.target = ''
        self.word_state = []
        self.state = 0
        self.guessed = []


def setup(client):
    client.add_cog(HangMan(client))
