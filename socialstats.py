#!./python3.5

from pytgbot import Bot
import json 
import requests
import configparser
import os
import sys

config = configparser.ConfigParser()
dir = os.path.dirname(sys.argv[0])
config.read(dir + 'socialstats.config')

BOT_TOKEN = config.get('telegram','BOT_TOKEN')
CHAT_ID = config.get('telegram','CHAT_ID')
bot = Bot(BOT_TOKEN)

googleapikey = config.get ('youtube','googleapikey')
channelid = config.get ('youtube','channelid')

truncatelimit = 25
dbFilePath = config.get('storage','ytdbFilePath')

url="https://www.googleapis.com/youtube/v3/search?key="+ googleapikey + "&channelId="+channelid+"&part=snippet&order=viewCount&maxResults=6"
r = requests.get(url)
data = json.loads(r.text)

videolist=""
for video in data['items']:
    try:
        videolist = videolist + video['id']['videoId'] + ","
    except KeyError:
        pass

url="https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id="+ videolist +"&key="+ googleapikey
r = requests.get(url)
data = json.loads(r.text)
with open(dbFilePath,'r') as dbFile:
    olddata = json.load(dbFile)

message = "Los 5 videos más visitados de tu canal: \n"
for video in data['items']:
    title = video['snippet']['localized']['title']
    videoid = video['id']
    views = video['statistics']['viewCount']
    try:
        viewsToday = str(int(views) - int(olddata[videoid]))
    except KeyError:
        viewsToday = "y al ser nuevo en el ranking, no se sabe cuantas"        
    message = message + "El video '"+ title[:truncatelimit] + (title[truncatelimit:] and "...") + "' se ha visto "+ views +" veces en total, " + viewsToday + " desde ayer.\n"
    olddata[videoid] = views
bot.send_message(CHAT_ID, message)

with open(dbFilePath,'w') as dbFile:
    json.dump(olddata,dbFile)
