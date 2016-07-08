import requests
from bs4 import BeautifulSoup as bs
import json
import datetime
from operator import itemgetter
import sys
from pytgbot import Bot
import configparser
import os
import time

config = configparser.ConfigParser()
scriptdir= os.path.dirname(sys.argv[0])
if scriptdir == "":
    scriptdir = os.getcwd()
conffile = scriptdir + '/socialstats.config'
config.read(conffile)

BOT_TOKEN = config.get('telegram','BOT_TOKEN')
CHAT_ID = config.get('telegram','CHAT_ID')
dbFilePath = scriptdir + "/" + config.get('storage','igdbFilePath')



#print(json.dumps(data,indent=2))

try:
    with open(dbFilePath,'r') as dbFile:
        fotos = json.load(dbFile)
except FileNotFoundError:
    print("Db file not found, we may be running for the first time. We'll create a new dbfile")
    fotos = {}

like_list={}
now = datetime.date.today().strftime('%Y%m%d')
limit=5
cursor=0
max_id=""
iguser = 'alquintopino'

while cursor < limit:
#    print(data['entry_data']['ProfilePage'][0]['user']['media']['page_info']['end_cursor'])
    r = requests.get('https://www.instagram.com/'+ iguser +'/'+max_id)
    p = bs(r.content,"html.parser")
    for script in p.find_all('script'):
        if 'window._sharedData' in script.text:
            data=json.loads(script.text[20:-1])
    if data['entry_data']['ProfilePage'][0]['user']['is_private'] == True:
        print("This account is private, I have no access to its data")
        sys.exit(0)
    for pic in data['entry_data']['ProfilePage'][0]['user']['media']['nodes']:
        picid = pic['code']
        likecountobj = {'date': now, 'likes': pic['likes']['count']}
        try:
            if fotos[picid]['likecount'][-1]['date'] == now:
                pass
            else:
                fotos[picid]['likecount'].append(likecountobj)        
            if len(fotos[picid]['likecount']) < 1:
                like_list[picid] = fotos[picid]['likecount'][-1]['likes'] - fotos[picid]['likecount'][-2]['likes']
            else:
                like_list[picid] = fotos[picid]['likecount'][-1]['likes']
        except KeyError:
            fotos[picid] = {'caption' : pic['caption'], 'dateposted' : pic['date'], 'likecount': [likecountobj], 'fullpic': pic['display_src'], 'thumbnail': pic['thumbnail_src']}
            like_list[picid] = likecountobj['likes']
    if data['entry_data']['ProfilePage'][0]['user']['media']['page_info']['has_next_page'] == True:
        max_id = "?max_id=" +data['entry_data']['ProfilePage'][0]['user']['media']['page_info']['end_cursor']
        cursor+=1
    else:
        #print("No has máy fotos!")
        break
#    print(cursor,data['entry_data']['ProfilePage'][0]['user']['media']['page_info']['end_cursor'] )
    time.sleep(1)
#    print(" ")
#    print("Vamos por la iteración numero " + str(cursor))

most_liked = sorted(like_list.items(), key=itemgetter(1), reverse=True)

i=0
message="Veamos tus likes desde ayer!\n\n"

while i < 5:
    if most_liked[i][1] > 0:

        pic=fotos[most_liked[i][0]]
        message=message + "'[" + ' '.join(pic['caption'][:30].splitlines()) + "...](https://instagram.com/p/"+ most_liked[i][0] +   \
                          ")' ganó *" + str(most_liked[i][1]) + "* likes (en total *" + str(pic['likecount'][-1]['likes']) +"*)\n\n"
    else:
        break
    i+=1

if i==0:
    pass
else:
    bot = Bot(BOT_TOKEN)
    bot.send_message(CHAT_ID, message, parse_mode='Markdown')
#    print(message)

try:
    os.rename(dbFilePath,dbFilePath+","+str(int(time.time())))
    with open(dbFilePath,'w') as dbFile:
        json.dump(fotos,dbFile)
except:
    print ("There was a problem writing the dbfile. Check permissions or disk space.")

 