import requests
from bs4 import BeautifulSoup as bs
import json
import datetime
from operator import itemgetter
import sys
from pytgbot import Bot
import configparser
import os

config = configparser.ConfigParser()
scriptdir= os.path.dirname(sys.argv[0])
if scriptdir == "":
    scriptdir = os.getcwd()
conffile = scriptdir + '/socialstats.config'
config.read(conffile)

BOT_TOKEN = config.get('telegram','BOT_TOKEN')
CHAT_ID = config.get('telegram','CHAT_ID')
dbFilePath = scriptdir + "/" + config.get('storage','igdbFilePath')

r = requests.get('https://www.instagram.com/alquintopino/')
p = bs(r.content,"html.parser")
for script in p.find_all('script'):
    if 'window._sharedData' in script.text:
        data=json.loads(script.text[20:-1])

#print(json.dumps(data,indent=2))


with open(dbFilePath,'r') as dbFile:
    fotos = json.load(dbFile)


most_liked={}
now = datetime.date.today().strftime('%Y%m%d')

for pic in data['entry_data']['ProfilePage'][0]['user']['media']['nodes']:
    likecount = pic['likes']['count']
    picid = pic['code']
    daycountobj = {'date': now, 'likes': likecount}
    try:
        if fotos[picid]['likecount'][-1]['date'] == now:
            pass
        else:
            fotos[picid]['likecount'].append(daycountobj)
        
        try:
            most_liked[picid] = fotos[picid]['likecount'][-1]['likes'] - fotos[picid]['likecount'][-2]['likes']
        except IndexError:
            most_liked[picid] = fotos[picid]['likecount'][-1]['likes']
    except KeyError:
        fotos[picid] = {'caption' : pic['caption'], 'dateposted' : pic['date'], 'likecount': fotos[picid]['likecount'], 'fullpic': pic['display_src'], 'thumbnail': pic['thumbnail_src']}
        most_liked[picid] = likecount

most_liked_sorted = sorted(most_liked.items(), key=itemgetter(1), reverse=True)
i=0
message=""
while i < 5:
    if most_liked_sorted[i][1] > 0:
        pic=fotos[most_liked_sorted[i][0]]
        message=message + "La foto '[" + ' '.join(pic['caption'][:25].splitlines()) + "](https://instagram.com/p/"+ most_liked_sorted[i][0] +   \
                          ")...' consiguió " + str(most_liked_sorted[i][1]) + " likes desde ayer. Tiene en total " + str(pic['likecount'][-1]['likes']) +".\n"
    i+=1

if message =="":
    pass
else:
    bot = Bot(BOT_TOKEN)
    bot.send_message(CHAT_ID, message, parse_mode='Markdown')
#    print(message)

#print(json.dumps(fotos,indent=2))
#    print(''.join(pic['caption'][:25].splitlines()) + ": " + str(pic['likes']['count']))
#sorted_output = sorted(output.items(), key=lambda x: x[1]['viewcount'],reverse=True)

#for pic in sorted_output[:5]:
#    type(pic)
#    print("La foto '" + pic[1]['caption'] + "'(https://instagram.com/p/"+ pic[0] + ") tiene " + str(pic[1]['viewcount']) + " likes.")

try:
    with open(dbFilePath,'w') as dbFile:
        json.dump(fotos,dbFile)
except:
    print ("There was a problem writing the dbfile. Check permissions or disk space.")