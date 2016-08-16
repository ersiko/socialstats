import sys
import configparser
import os
import json
import elasticsearch
import datetime 
import telepot
import urllib
from elasticsearch_dsl import Search

config = configparser.ConfigParser()
scriptdir= os.path.dirname(sys.argv[0])
if scriptdir == "":
    scriptdir = os.getcwd()
conffile = scriptdir + '/socialstats.config'
config.read(conffile)
BOT_TOKEN = config.get('telegram','BOT_TOKEN')
bot = telepot.Bot(BOT_TOKEN)
es_server = config.get('elasticsearch','server')
es = elasticsearch.Elasticsearch([es_server])

res=es.search(index='ourusers',doc_type='users')

index_suffix=datetime.date.today().strftime("%Y%m%d")

for user in res['hits']['hits']:
    telegram_id=user['_id']
    for iguser in user['_source']['subscribed_to']:
        message = ""
        print("El usuario " + user['_source']['username'] + " sigue a " + iguser)
#        res2 = es.get(index='ourusers', doc_type='last_updated', id=telegram_id)
#        for regularity in ['1','3','7','30','90','180','365']:
#            timestamp = int(res2['_source']['date'+regularity])/1000
#            last_updated = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
#            days_ago = datetime.datetime.now() - datetime.datetime.fromtimestamp(timestamp)
#            if days_ago.days >= int(regularity):
#                print("Toca enviarle el de los " + str(regularity) + " días.")
#            else:#
#                print("Han pasado solo " + str(days_ago) + " días, aún falta para los " + str(regularity))

 #       res3 = es.get(index='igusers', doc_type='followers_diffs', id=iguser)
 #       for key, value in res3['_source'].items():
 #           print(iguser+ " consiguió " + str(value) + " followers en los ultimos " + str(key) + " dias")
            #bot.sendMessage(telegram_id,iguser+ " consiguió " + str(value) + " followers en los ultimos " + str(key) + " dias")
        following=es.get(index="igusers",doc_type="following_diffs", id=iguser)['_source']['1']
        followers=es.get(index="igusers",doc_type="followers_diffs", id=iguser)['_source']['1']
        for pic in es.search(index='pics', doc_type='likes_diffs', q="igusername:"+iguser, sort='1:desc', size='5')['hits']['hits']:
            if pic['_source']['1'] > 0:
                total = es.get(index='picsdaily-'+ index_suffix,doc_type='likes',id=pic['_id'])['_source']['number']
                caption=es.get(index='pics', doc_type='pics', id=pic['_id'])['_source']['caption']
                message=message + "\n'[" + ' '.join(caption[:30].splitlines()) + "...](https://instagram.com/p/"+ pic['_id'] +   \
                              ")' ganó *" + str(pic['_source']['1']) + "* likes (en total *" + str(total) +"*)\n"
        if following != 0 or followers != 0:
            message = message + "\nDiferencia de seguidores: " + str(followers) + ". Diferencia de seguidos: " + str(following)
                #message = message + "\n" + "La foto " + pic['_id'] + " tuvo " + str(pic['_source']['1']) + " likes desde ayer."
        if message != "":
            message = "Veamos tus likes de hoy!\n" + message
            bot.sendMessage(telegram_id,message,parse_mode='Markdown')
#        pics=es.search(index='pics', doc_type='pics', q="username:"+iguser)
#        print("Del usuario "+iguser+" tenemos las siguientes fotos: ")
        #bot.sendMessage(telegram_id,"Del usuario "+iguser+" tenemos las siguientes fotos: ")
#        for pic in pics['hits']['hits']:
            #print(pic['_id'])
#            print(pic['_source']['thumbnail'])

#            thumb = urllib.request.urlopen(pic['_source']['thumbnail'])
#            filename = urllib.parse.urlsplit(pic['_source']['thumbnail']).path.split('/')[-1]
#            print("Enviando " + filename)
#            bot.sendPhoto(telegram_id,(filename,thumb))
            #(telegram_id,pic['_source']['thumbnail'])
