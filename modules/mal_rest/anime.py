import requests

class Anime:
    def __init__(self, id=None, data=None):
        self.mal_url = ''
        self.image_url = ''
        self.title = ''
        self.english_title = ''
        self.alt_titles = ''
        self.source = ''
        self.ep_num = 0
        self.air_period = ''
        self.rating = 0.0
        self.rank = 1
        self.synopsis = ''
        self.studio = ''
        self.genres = []
        self.ops = []
        self.members = 0
        if id == None:
            self.image_url = data['image_url']
            self.rank = data['rank']
            self.mal_url = data['url']
            self.rating = data['score']
            self.members = data['members']
            self.title = data['title']
        else:
            self.mal_id = id
            self.get_anime_info()
    
    def get_anime_info(self):
        endpoint = 'https://api.jikan.moe/v3/anime/' + str(self.mal_id)
        response = requests.get(url=endpoint, headers={'User-agent': 'meh bot 1.0'}).json()
        self.mal_url = response['url']
        self.image_url = response['image_url']
        self.title = response['title']
        self.english_title = response['title_english']
        self.alt_titles = response['title_synonyms']
        self.source = response['source']
        self.ep_num = response['episodes']
        self.members = response['members']
        self.air_period = response['aired']['string']
        self.rating = response['score']
        self.rank = response['rank']
        self.synopsis = response['synopsis']
        #self.studio = response['studios'][0]['name']
        if len(response['studios']) > 0:
            self.studio = response['studios'][0]['name']
        else:
            self.studio = ''
        self.ops = response['opening_themes']
        for genre in response['genres']:
            self.genres.append(genre['name'])

    def is_similar(self, name):
        name = name.lower()
        print(name)
        if name in self.title.lower() or self.english_title != None and name in self.english_title.lower():
            return True
        else:
            for alt_title in self.alt_titles:
                if name in alt_title.lower():
                    return True
            
            return False