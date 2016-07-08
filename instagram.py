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
import types

config = configparser.ConfigParser()
scriptdir= os.path.dirname(sys.argv[0])
if scriptdir == "":
    scriptdir = os.getcwd()
conffile = scriptdir + '/socialstats.config'
config.read(conffile)

BOT_TOKEN = config.get('telegram','BOT_TOKEN')
CHAT_ID = config.get('telegram','CHAT_ID')
igusers = config.items('instagram')
dbFilePath = scriptdir + "/" + config.get('storage','igdbFilePath')

bot = Bot(BOT_TOKEN)

#print(json.dumps(data,indent=2))

try:
    with open(dbFilePath,'r') as dbFile:
        fotos = json.load(dbFile)
except FileNotFoundError:
    print("Db file not found, we may be running for the first time. We'll create a new dbfile")
    fotos = {}

now = datetime.date.today().strftime('%Y%m%d')
limit=1

#iguser = 'alquintopino'

#fotos={}
for iguser, telegram_id in igusers:

    cursor=0
    max_id=""
    like_list={}
    try:
        pics=fotos[iguser]['pics']
    except KeyError:
        fotos[iguser]={}
        fotos[iguser]['telegram_id']=telegram_id
        fotos[iguser]['pics']={}
        fotos[iguser]['followed_by']=[]
        fotos[iguser]['follows']=[]
        fotos[iguser]['private']=False
        pics={}
    while cursor < limit:
#    print(data['entry_data']['ProfilePage'][0]['user']['media']['page_info']['end_cursor'])
        r = requests.get('https://www.instagram.com/'+ iguser +'/'+max_id)
        p = bs(r.content,"html.parser")
        for script in p.find_all('script'):
            if 'window._sharedData' in script.text:
                data=json.loads(script.text[20:-1])
        if data['entry_data']['ProfilePage'][0]['user']['is_private'] == True:
            print("This account is private, I have no access to its data")
            break
        for pic in data['entry_data']['ProfilePage'][0]['user']['media']['nodes']:
            picid = pic['code']
            likecountobj = {'date': now, 'likes': pic['likes']['count']}
            try:
                if pics[picid]['likecount'][-1]['date'] == now:
                    pass
                else:
                    pics[picid]['likecount'].append(likecountobj)        
                if len(pics[picid]['likecount']) < 1:
                    like_list[picid] = pics[picid]['likecount'][-1]['likes'] - pics['likecount'][-2]['likes']
                else:
                    like_list[picid] = pics[picid]['likecount'][-1]['likes']
            except KeyError:
                pics[picid] = {'caption' : pic['caption'], 'dateposted' : pic['date'], 'likecount': [likecountobj], 'fullpic': pic['display_src'], 'thumbnail': pic['thumbnail_src']}
                like_list[picid] = likecountobj['likes']
        if data['entry_data']['ProfilePage'][0]['user']['media']['page_info']['has_next_page'] == True:
            max_id = "?max_id=" +data['entry_data']['ProfilePage'][0]['user']['media']['page_info']['end_cursor']
            cursor+=1
        else:
        #print("No has máy fotos[iguser]!")
            break
#    print(cursor,data['entry_data']['ProfilePage'][0]['user']['media']['page_info']['end_cursor'] )
        time.sleep(1)
#    print(" ")
#    print("Vamos por la iteración numero " + str(cursor))

    followedcountobj = {'date': now, 'likes': data['entry_data']['ProfilePage'][0]['user']['followed_by']['count']}
    followscountobj = {'date': now, 'likes': data['entry_data']['ProfilePage'][0]['user']['follows']['count']}
    fotos[iguser]['followed_by'].append(followedcountobj)
    fotos[iguser]['follows'].append(followscountobj)
    fotos[iguser]['pics'] = pics

    most_liked = sorted(like_list.items(), key=itemgetter(1), reverse=True)

    i=0
    message="Veamos tus likes desde ayer!\n\n"

    while i < 5 and i < len(most_liked):
        if most_liked[i][1] > 0:
            pic=pics[most_liked[i][0]]
            message=message + "'[" + ' '.join(pic['caption'][:30].splitlines()) + "...](https://instagram.com/p/"+ most_liked[i][0] +   \
                              ")' ganó *" + str(most_liked[i][1]) + "* likes (en total *" + str(pic['likecount'][-1]['likes']) +"*)\n\n"
        else:
            break
        i+=1

    if i==0: 
        pass
    else:
#        print('escribiendo al canal'+fotos[iguser]['telegram_id'])
        bot.send_message(fotos[iguser]['telegram_id'], message, parse_mode='Markdown')
#    print(message)
try:
#    os.rename(dbFilePath,dbFilePath+","+str(int(time.time())))
    with open(dbFilePath,'w') as dbFile:
        json.dump(fotos,dbFile)
except:
    print ("There was a problem writing the dbfile. Check permissions or disk space.")

 
 

