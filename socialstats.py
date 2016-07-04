#!./python3.5
import datetime
from pytgbot import Bot
import json 
import requests
import configparser
import os
import sys
from operator import itemgetter


config = configparser.ConfigParser()
scriptdir= os.path.dirname(sys.argv[0])
if scriptdir == "":
    scriptdir = os.getcwd()
conffile = scriptdir + '/socialstats.config'
config.read(conffile)

BOT_TOKEN = config.get('telegram','BOT_TOKEN')
CHAT_ID = config.get('telegram','CHAT_ID')
bot = Bot(BOT_TOKEN)

googleapikey = config.get ('youtube','googleapikey')
channelid = config.get ('youtube','channelid')

truncatelimit = 25
dbFilePath = scriptdir + "/" + config.get('storage','ytdbFilePath')

url="https://www.googleapis.com/youtube/v3/search?key="+ googleapikey + "&channelId="+channelid+"&type=video&part=snippet&order=viewCount&maxResults=50"
r = requests.get(url)
data = json.loads(r.text)

videolist=""
for video in data['items']:
    videolist = videolist + video['id']['videoId'] + ","

url="https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id="+ videolist +"&key="+ googleapikey
r = requests.get(url)
data = json.loads(r.text)
try:
    with open(dbFilePath,'r') as dbFile:
        olddata = json.load(dbFile)
except FileNotFoundError:
    print("Db file not found, we may be running for the first time. We'll create a new dbfile")
    olddata = {}

now = datetime.date.today().strftime('%Y%m%d')
most_viewed={}
#message = "Los 5 videos más visitados de tu canal: \n"
for video in data['items']:
    title = video['snippet']['localized']['title']
    videoid = video['id']
    #print(json.dumps(video,indent=2))
    viewcount = video['statistics']['viewCount']
    daycountobj = {'date': now, 'views': viewcount}
    try:
        if olddata[videoid]['viewcount'][-1]['date'] == now:
             pass
        else:
            olddata['videoid']['viewcount'].append(daycountobj)
        try:
            most_viewed[videoid] = olddata[videoid]['viewcount'][-1]['likes'] - olddata['picid']['viewcount'][-2]['likes']
        except IndexError:
            most_viewed[videoid] = olddata[videoid]['viewcount'][-1]['likes']
    except KeyError:
#        print(video['snippet']['description'])
        olddata[videoid] = {'description' : video['snippet']['description'], 'dateposted' : video['snippet']['publishedAt'], 'viewcount': [daycountobj], 'title': video['snippet']['title'], 'thumbnail': video['snippet']['thumbnails']['high']['url']}
        most_viewed[videoid] = int(viewcount)

    #message = message + "El video '"+ title[:truncatelimit] + (title[truncatelimit:] and "...") + "' se ha visto "+ views +" veces en total, " + viewsToday + " desde ayer.\n"

most_viewed_sorted = sorted(most_viewed.items(), key=itemgetter(1), reverse=True)
#print(most_viewed_sorted)
i=0
message=""
while i < 5:
    video=olddata[most_viewed_sorted[i][0]]
    #print(vid)
    if most_viewed_sorted[i][1] > 0:
        message=message + "El video '" + video['title'][:truncatelimit] + (video['title'][truncatelimit:] and "...") + \
                      "' (https://www.youtube.com/watch?v="+ most_viewed_sorted[i][0] + ") fue visto " + str(most_viewed_sorted[i][1]) + \
                      " veces desde ayer. Tiene en total " + video['viewcount'][-1]['views'] +".\n"
    i+=1

if message == "":
    pass
else:
    print(message)
#   bot.send_message(CHAT_ID, message)

try:
    with open(dbFilePath,'w') as dbFile:
        json.dump(olddata,dbFile)
except:
    print ("There was a problem writing the dbfile. Check permissions or disk space.")