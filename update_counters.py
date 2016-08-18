import sys
import configparser
import os
import json
import igscrape
import elasticsearch
from elasticsearch_dsl import Search
from datetime import date, timedelta
import time

config = configparser.ConfigParser()
scriptdir= os.path.dirname(sys.argv[0])
if scriptdir == "":
    scriptdir = os.getcwd()
conffile = scriptdir + '/socialstats.config'
config.read(conffile)

es_server = config.get('elasticsearch','server')

es = elasticsearch.Elasticsearch([es_server])

res=es.search(index='igusers',doc_type='users')


index_suffix_today=date.today().strftime("%Y%m%d")
index_suffix_yesterday=(date.today()-timedelta(days=1)).strftime("%Y%m%d")
timestamp_today = date.today().strftime("%s")+"000"
timestamp_yesterday = (date.today()-timedelta(days=1)).strftime("%s")+"000"

for iguser in res['hits']['hits']:
    print("usuario " + iguser['_id'])
    my_followers_update = {}
    my_following_update = {}
    for period in ['1','3','7','30','90','180','365']:
        my_follows=es.search(index="userdaily-last-" + period + "-days",doc_type="follows",q="_id:"+iguser['_id'])['hits']['hits']
        if len(my_follows) == 1:
            # El usuario se ha dado de alta ahora y no tenemos datos de ayer. Mañana podremos calcular.
            break
        else:
            my_followers_update[period] = my_follows[-1]['_source']['followers'] - my_follows[0]['_source']['followers']
            my_following_update[period] = my_follows[-1]['_source']['following'] - my_follows[0]['_source']['following']
    update = es.update(index="igusers", doc_type="following_diffs", id=iguser['_id'], body={"doc":my_following_update,'doc_as_upsert':True})
    update = es.update(index="igusers", doc_type="followers_diffs", id=iguser['_id'], body={"doc":my_followers_update,'doc_as_upsert':True})

    data, maxid = igscrape.get_iguser_data(iguser['_id'], 2)
    for pic in data['entry_data']['ProfilePage'][0]['user']['media']['nodes']:
        pic_id = pic['code']
        print("Foto: " +pic_id)
        my_likes_update = {}
        for period in ['1','3','7','30','90','180','365']:
            my_likes=es.search(index="picsdaily-last-" + period + "-days",doc_type="likes",q="_id:"+pic_id)['hits']['hits']
            if len(my_likes) == 1 or len(my_likes) == 0:
                # La foto es vieja y se acaba de añadir. No tenemos datos de ayer. Mañana podremos calcular.
                break
            else:
                my_likes_update[period] = my_likes[-1]['_source']['number'] - my_likes[0]['_source']['number']
        update = es.update(index='pics', doc_type='likes_diffs', id=pic_id, body={"doc":my_likes_update,'doc_as_upsert':True})



