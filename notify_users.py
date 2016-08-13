import sys
import configparser
import os
import json
import elasticsearch
from datetime import date
import telepot
import urllib

config = configparser.ConfigParser()
scriptdir= os.path.dirname(sys.argv[0])
if scriptdir == "":
    scriptdir = os.getcwd()
conffile = scriptdir + '/socialstats.config'
config.read(conffile)
BOT_TOKEN = config.get('telegram','BOT_TOKEN')
bot = telepot.Bot(BOT_TOKEN)
es = elasticsearch.Elasticsearch(['10.8.0.1'])

res=es.search(index='ourusers')

index_suffix=date.today().strftime("%Y%m%d")

for user in res['hits']['hits']:
    telegram_id=user['_id']
    for iguser in user['_source']['subscribed_to']:
        print("El usuario " + user['_source']['username'] + " sigue a " + iguser)
        res = es.get(index='igusers', doc_type='followers_diffs', id=iguser)
        for key, value in res['_source'].items():
            print(iguser+ " consiguió " + str(value) + " followers en los ultimos " + str(key) + " dias")
            #bot.sendMessage(telegram_id,iguser+ " consiguió " + str(value) + " followers en los ultimos " + str(key) + " dias")
        pics=es.search(index='pics', doc_type='pics', q="username:"+iguser)
        print("Del usuario "+iguser+" tenemos las siguientes fotos: ")
        bot.sendMessage(telegram_id,"Del usuario "+iguser+" tenemos las siguientes fotos: ")
        for pic in pics['hits']['hits']:
            print(pic['_source']['thumbnail'])
            thumb = urllib.request.urlopen(pic['_source']['thumbnail'])
            filename = urllib.parse.urlsplit(pic['_source']['thumbnail']).path.split('/')[-1]
            print("Enviando " + filename)
            bot.sendPhoto(telegram_id,(filename,thumb))
            #(telegram_id,pic['_source']['thumbnail'])
