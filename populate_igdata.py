# -*- coding: utf-8 -*-

import sys
import configparser
import os
import json
import igscrape
import elasticsearch
from elasticsearch_dsl import Search
from datetime import date, timedelta
import time

start=time.time()

config = configparser.ConfigParser()
scriptdir= os.path.dirname(sys.argv[0])
if scriptdir == "":
    scriptdir = os.getcwd()
conffile = scriptdir + '/socialstats.config'
config.read(conffile)

es_server = config.get('elasticsearch','server')

es = elasticsearch.Elasticsearch([es_server])

def create_snapshot(es,suffix):
    snapshot=elasticsearch.client.SnapshotClient(es)
    snapshot_res = snapshot.create('instagramstats_backup',index_suffix_today+"-"+suffix, wait_for_completion=True)

def update_index_aliases(es):
    for my_range in ['1','3','7','30','90','180','365']:
        my_date=(date.today()-timedelta(days=int(my_range)+1)).strftime("%Y%m%d")
        for my_index in ['pics', 'user']:
            #print("Voy a añadir el indice "+my_index+"daily-"+index_suffix_today+" al indice "+my_index+"daily-last-" + my_range + "-days")
            aliasupdate_res=es.indices.put_alias(my_index+"daily-"+index_suffix_today, my_index+"daily-last-" + my_range + "-days")
            if es.indices.exists_alias(my_index+"daily-"+my_date , my_index+"daily-last-" + my_range + "-days"):
                #print("Voy a quitar el indice "+my_index+"-daily-"+my_date+" del alias daily-last-" + my_range + "-days")
                es.indices.delete_alias(my_index+"daily-"+my_date , my_index+"daily-last-" + my_range + "-days")

def update_user_counters(es, iguser):
    my_followers_update = {}
    my_following_update = {}
    for period in ['1','3','7','30','90','180','365']:
        #print("my_follows=es.search(index=\"userdaily-last-" + period + "-days\",doc_type=\"follows\",q=\"_id:"+iguser['_id'])  
        my_follows=es.search(index="userdaily-last-" + period + "-days",doc_type="follows",q="_id:"+iguser)['hits']['hits']
        if len(my_follows) == 1:
            # El usuario se ha dado de alta ahora y no tenemos datos de ayer. Manana podremos calcular.
            break
        else:
            my_followers_update[period] = my_follows[-1]['_source']['followers'] - my_follows[0]['_source']['followers']
            my_following_update[period] = my_follows[-1]['_source']['following'] - my_follows[0]['_source']['following']
    print("Le voy a poner al usuario " + iguser + " el siguiente dict de follows: " + str(my_following_update) + " Y de following: " + str(my_followers_update))
    update = es.update(index="igusers", doc_type="following_diffs", id=iguser, body={"doc":my_following_update,'doc_as_upsert':'true'})
    update = es.update(index="igusers", doc_type="followers_diffs", id=iguser, body={"doc":my_followers_update,'doc_as_upsert':'true'})


def update_pic_counters(es, pic,igusername):
    for pic in data['entry_data']['ProfilePage'][0]['user']['media']['nodes']:
        pic_id = pic['code']
        print("Foto: " +pic_id)
        my_likes_update = {}
        for period in ['1','3','7','30','90','180','365']:
            my_likes=es.search(index="picsdaily-last-" + period + "-days",doc_type="likes",body={"query": { "match": { "_id":pic_id}}})['hits']['hits']
#            print("Likes: "+str(my_likes)+ " " + str(len(my_likes)))
            if len(my_likes) == 1 or len(my_likes) == 0:
                # La foto es vieja y se acaba de anadir. No tenemos datos de ayer. Manana podremos calcular.
                break
            else:
                print("voy a calcular")
                my_likes_update[period] = my_likes[-1]['_source']['number'] - my_likes[0]['_source']['number']
        if my_likes_update != {}:
            my_likes_update['igusername'] = igusername
            print("Le voy a poner a la foto " + pic_id + " el dict " + str(my_likes_update))
            update = es.update(index='pics', doc_type='likes_diffs', id=pic_id, body={"doc":my_likes_update,'doc_as_upsert':'true'})
        #print(update)

def update_todays_user_follows(es,data,iguser):
    followers = data['entry_data']['ProfilePage'][0]['user']['followed_by']['count']
    following = data['entry_data']['ProfilePage'][0]['user']['follows']['count']
    print("Le voy a poner al usuario" + iguser + " " + str(followers) + " followers y " + str(following) + " following")
    es.index(index='userdaily-'+index_suffix_today,doc_type='follows', id=iguser,body={'followers':followers, 'following': following, 'timestamp': timestamp_today})

def add_pic(es,pic,igusername):
    dateposted = pic['date']*1000
    thumbnail = pic['thumbnail_src']
    fullpic = pic['display_src']
    caption = pic['caption']
    pic_id = pic['code']
    likes = pic['likes']['count']
    #print("Username " + igusername + " posted pic "+ pic_id + " on " + str(dateposted) + 
    #      " and it has " + str(likes) + " likes. You can see a thumbnail at " + thumbnail + 
    #      " and the full pic at " + fullpic + ". The caption is " + caption)
    pic_object = {'username': igusername, 'dateposted': dateposted, 'thumbnail': thumbnail, 'fullpic' : fullpic, 'caption': caption}
    print("Doy de alta la foto " + pic_id + " con el doc " + str(pic_object))
    es.index(index='pics', doc_type='pics', id=pic_id, body=pic_object)
    if dateposted > int(timestamp_yesterday):
        print("Es una foto que se acaba de publicar. Le pongo 0 likes el dia anterior")
        es.index(index='picsdaily-' +index_suffix_yesterday,doc_type='likes', id=pic_id,body={'number':0, 'timestamp': timestamp_yesterday, 'iguser': igusername})
    else: 
        print("Es una foto antigua que se acaba de importar. Dejo los likes anteriores como 'indeterminados'")
    print("Y ahora le pong a la foto "+pic_id+" " +str(likes) + " likes para el dia de hoy")
    es.index(index='picsdaily-' +index_suffix_today,doc_type='likes', id=pic_id,body={'number':likes, 'timestamp': timestamp_today, 'iguser': igusername})


def update_todays_pics_likes(es,data,igusername):

    for pic in data['entry_data']['ProfilePage'][0]['user']['media']['nodes']:
        pic_id = pic['code']
        print("update_todays_Pics_likes Foto " +pic_id)
        likes = pic['likes']['count']
        if not es.exists(index="pics", doc_type="pics", id=pic_id):
#            print("la foto es nueva")
            add_pic(es,pic,igusername)
        else:
        #    print("La foto " + pic_id + " ya está en elasticsearch")
            days=0
            index_daily=(date.today()-timedelta(days=days)).strftime("%Y%m%d")

            if es.search(index="picsdaily-*", doc_type='likes', body={"query": { "match": { "_id":pic_id}}}, size=0)['hits']['total'] == 0:
                result = es.index(index='picsdaily-' +index_daily,doc_type='likes', id=pic_id,body={'number':likes, 'timestamp': timestamp_daily, 'iguser': igusername})
            else: 
                while not es.exists(index="picsdaily-"+index_daily, doc_type='likes', id=pic_id):
                    timestamp_daily = (date.today()-timedelta(days=days)).strftime("%s")+"000"
                    #print("Dias = "+str(days)+" . Le pongo " + str(likes) + " likes a la foto " + str(pic_id))
                    result = es.index(index='picsdaily-' +index_daily,doc_type='likes', id=pic_id,body={'number':likes, 'timestamp': timestamp_daily, 'iguser': igusername})
                    days+=1
                    index_daily=(date.today()-timedelta(days=days)).strftime("%Y%m%d")



#create_snapshot(es, "before")

res=es.search(index='igusers',doc_type='users')

index_suffix_today=date.today().strftime("%Y%m%d")
index_suffix_yesterday=(date.today()-timedelta(days=1)).strftime("%Y%m%d")
timestamp_today = date.today().strftime("%s")+"000"
timestamp_yesterday = (date.today()-timedelta(days=1)).strftime("%s")+"000"

es.indices.create(index="picsdaily-"+index_suffix_today)
es.indices.create(index="userdaily-"+index_suffix_today)
update_index_aliases(es)

for iguser in res['hits']['hits']:
    print(iguser['_id'])
    print("scrape")
    data, maxid = igscrape.get_iguser_data(iguser['_id'], 10)
    print("update daily follows")
    update_todays_user_follows(es,data,iguser['_id'])
    print("update daily likes")
    update_todays_pics_likes(es,data,iguser['_id'])
    time.sleep(1)
    print("Calculate pic likes_diffs")
    update_pic_counters(es, data,iguser['_id'])
    print("Calculate user follow_diffs")
    update_user_counters(es,iguser['_id'])

#create_snapshot(es, "after")
print(str(time.time()-start))