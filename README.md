# MehBot
A discord bot written in Python that is mainly centered around getting information from the internet. It has been dockerized for easy deployment and uses MongoDB to persist relevant data.
# Features
- Get posts from Reddit
- Start a Reddit feed in a channel
- Get definitions, synonyms, or words that rhyme
- Integration with MAL to get information about anime
- Play music from YouTube in a voice channel and add songs to a stack
- Download music from YouTube in an mp3 format
- Play hangman
- Create a personal list of favorite Anime unique to each user

# Running the Bot
Since this project has been dockerized, getting it up and running is a lot easier as you do not have to install all of the dependencies required individually. That said, you will need Docker and Git installed on your machine. This project runs with two containers, one with the MongoDB image and another with an Ubuntu image that will run the bot.

First, clone the project onto your machine
```
git clone https://github.com/meh430/MehBot.git
```
Cd into the project directory and open up the config.py file that looks like this:
```python
# Replace BOT TOKEN with your bot token
BOT_TOKEN  =  "BOT TOKEN"

# Replace the 0 with the id of a channel you would like to use as the Reddit feed
REDDIT_FEED_ID  =  0

MONGO_URL  =  "mongodb://localhost:27017/"
```
Now, follow the instructions [here](https://discordpy.readthedocs.io/en/latest/discord.html). Make sure to give the bot 'administrator' permissions. After that, copy the bot token and paste it into the config.py file as a string.

Finally, run this command to start the bot
```
docker-compose up --build
```

The bot should be online now.
