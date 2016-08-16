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
    s=Search(using=es, index="userdaily*").query("match", _id=iguser['_id'])
    s.aggs.bucket('followers_por_dia','date_histogram', field='timestamp',interval='day').metric('followers','min',field='followers').pipeline('daily_diff','serial_diff', buckets_path='followers', lag=1)
    followers_res = s.execute()
    s=Search(using=es, index="userdaily*").query("match", _id=iguser['_id'])
    s.aggs.bucket('following_por_dia','date_histogram', field='timestamp',interval='day').metric('following','min',field='following').pipeline('daily_diff','serial_diff', buckets_path='following', lag=1)
    following_res = s.execute()
    try:
        followers_diff = followers_res.aggregations['followers_por_dia']['buckets'][-1]['daily_diff']['value']
        following_diff = following_res.aggregations['following_por_dia']['buckets'][-1]['daily_diff']['value']
        update = es.update(index="igusers", doc_type="following_diffs", id=iguser['_id'], body={"doc":{1:int(following_diff)}})
        update = es.update(index="igusers", doc_type="followers_diffs", id=iguser['_id'], body={"doc":{1:int(followers_diff)}})
        print("El usuario " + iguser['_id'] + " ha ganado " + str(followers_diff) + " followers desde ayer y sigue a " + str(following_diff) + " personas más." )
    except KeyError:
        howmanytimes = es.search(index='userdaily*', doc_type='follows', q='_id:'+iguser['_id'])['hits']['total']
        if howmanytimes == 1:
            print("Es una usuario que se acaba de añadir. Le pongo 0 y Mañana se actualizará.")
            update = es.update(index="igusers", doc_type="following_diffs", id=iguser['_id'], body={"doc":{1:0},'doc_as_upsert':True})
            update = es.update(index="igusers", doc_type="followers_diffs", id=iguser['_id'], body={"doc":{1:0},'doc_as_upsert':True})
            print("El usuario " + iguser['_id'] + " se acaba de añadir. Le ponemos 0 followers y following" )
        else:
            print("No se que pasa")
            sys.exit()
        


#    print(res.to_dict())

    data, maxid = igscrape.get_iguser_data(iguser['_id'], 2)
    for pic in data['entry_data']['ProfilePage'][0]['user']['media']['nodes']:
        pic_id = pic['code']

        #if result['created'] == False:
        #    dont_bother_trying_to_add_the_rest_of_likes = True
        print("vamos por " +pic_id, end="", flush=True)
        s=Search(using=es, index="picsdaily*").query("match", _id=pic_id)
        s.aggs.bucket('likes_por_dia','date_histogram', field='timestamp',interval='day').metric('likes','min',field='number').pipeline('daily_diff','serial_diff', buckets_path='likes', lag=1)
        respics = s.execute()
        try:
            likediff = respics.aggregations['likes_por_dia']['buckets'][-1]['daily_diff']['value']
            print("y desde ayer tuvo " + str(likediff) + " likes, los pongo en elasticsearch")
            update = es.update(index='pics', doc_type='likes_diffs', id=pic_id, body={"doc":{1:int(likediff), 'igusername': iguser['_id']},'doc_as_upsert':True})
        except KeyError:
            howmanytimes = es.search(index='picsdaily*', doc_type='likes', q='_id:'+pic_id)['hits']['total']
            if howmanytimes == 1:
                print("Es una foto antigua que se acaba de añadir. Mañana se actualizará.")
            else:
                res3pics = es.get(index="pics", doc_type="pics", id=pic_id)
                res2pics = es.search(index="picsd*", doc_type="likes", q="_id:"+pic_id)
                print("La foto era " + pic_id + " y el contenido es " + str(res3pics))
                print("Y los likes son" + str(res2pics))
                sys.exit()
