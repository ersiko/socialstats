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

def create_snapshot(es):
    snapshot=elasticsearch.client.SnapshotClient(es)
    res = snapshot.create('instagramstats_backup',index_suffix_today)

def update_index_aliases(es):
    for my_range in ['1','3','7','30','90','180','365']:
        my_date=(date.today()-timedelta(days=int(my_range)+1)).strftime("%Y%m%d")
        for my_index in ['pics', 'user']:
            es.indices.put_alias(my_index+"daily-"+index_suffix_today, my_index+"daily-last-" + my_range + "-days")
            if es.indices.exists_alias(my_index+"daily-"+my_date , my_index+"daily-last-" + my_range + "-days"):
                es.indices.delete_alias(my_index+"daily-"+my_date , my_index+"daily-last-" + my_range + "-days")

def update_counters(es, iguser):
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



res=es.search(index='igusers',doc_type='users')

index_suffix_today=date.today().strftime("%Y%m%d")
index_suffix_yesterday=(date.today()-timedelta(days=1)).strftime("%Y%m%d")
timestamp_today = date.today().strftime("%s")+"000"
timestamp_yesterday = (date.today()-timedelta(days=1)).strftime("%s")+"000"


for iguser in res['hits']['hits']:
    print(iguser['_id'])
    dont_bother_trying_to_add_the_rest_of_likediffs = False
    dont_bother_trying_to_add_the_rest_of_likes = False
    dont_bother_trying_to_add_the_rest_of_pics = False
    data, maxid = igscrape.get_iguser_data(iguser['_id'], 10)
    igusername = iguser['_id']
    followers = data['entry_data']['ProfilePage'][0]['user']['followed_by']['count']
    following = data['entry_data']['ProfilePage'][0]['user']['follows']['count']

#    following_diff={}
#    followers_diff={}
    #print("es.index(index='userdaily-'" +index_suffix+",doc_type='follows', id="+igusername+",body={'followers':"+str(followers)+", 'following': "+str(following)+"})")
    es.index(index='userdaily-'+index_suffix_today,doc_type='follows', id=igusername,body={'followers':followers, 'following': following, 'timestamp': timestamp_today})
#    oldvalue={'following': following, 'followers': followers}
#    oldest_index_found = False
#    for diff_days in [1,3,7,30,90,180,365]:
#        compared_date=date.today()-timedelta(days=diff_days)
#        suffix=compared_date.strftime("%Y%m%d")
##        if not oldest_index_found:
#            if es.exists(index='userdaily-'+suffix, doc_type='follows', id=igusername):
#                oldvalue = es.get(index='userdaily-'+suffix, doc_type='follows', id=igusername)['_source']
#            else:
#                oldest_index_found = True
#        following_diff[diff_days] = following - oldvalue['following']
#        followers_diff[diff_days] = followers - oldvalue['followers']

#    print("Followers" + str(followers_diff) + " y follows " +str(following_diff))
    #print("es.index(index='igusers', doc_type='followers_diffs', id="+igusername+", body="+str(followers_diff)+")")
#    es.index(index='igusers', doc_type='followers_diffs', id=igusername, body=followers_diff)
    #print("es.index(index='igusers', doc_type='following_diffs', id="+igusername+", body="+str(following_diff)+")")
#    es.index(index='igusers', doc_type='following_diffs', id=igusername, body=following_diff)
    for pic in data['entry_data']['ProfilePage'][0]['user']['media']['nodes']:
        pic_id = pic['code']
        likes = pic['likes']['count']

        #Añadir fotos nuevas a instagram

        #if dont_bother_trying_to_add_the_rest_of_pics:
            #print("Como ya he detectado una foto insertada, y van por orden, pues ya no intento insertar más, porque el resto ya lo estarán.")
        #    pass
        #else:
        if not es.exists(index="pics", doc_type="pics", id=pic_id):
            dateposted = pic['date']*1000
            thumbnail = pic['thumbnail_src']
            fullpic = pic['display_src']
            caption = pic['caption']
            print("Username " + igusername + " posted pic "+ pic_id + " on " + str(dateposted) + 
              " and it has " + str(likes) + " likes. You can see a thumbnail at " + thumbnail + 
              " and the full pic at " + fullpic + ". The caption is " + caption)
            pic_object = {'username': igusername, 'dateposted': dateposted, 'thumbnail': thumbnail, 'fullpic' : fullpic, 'caption': caption}
            #print("es.index(index='pics', doc_type='pics', id="+pic_id+", body="+str(pic_object)+")")
            es.index(index='pics', doc_type='pics', id=pic_id, body=pic_object)
            if dateposted > int(timestamp_yesterday):
                print("Es una foto que se acaba de publicar. Le pongo 0 likes el dia anterior")
                es.index(index='picsdaily-' +index_suffix_yesterday,doc_type='likes', id=pic_id,body={'number':0, 'timestamp': timestamp_yesterday})
            else: 
                print("Es una foto antigua que se acaba de importar. Dejo los likes anteriores como 'indeterminados'")
            es.index(index='picsdaily-' +index_suffix_today,doc_type='likes', id=pic_id,body={'number':likes, 'timestamp': timestamp_today})

        else:
            print("La foto " + pic_id + " ya está en elasticsearch")
        #    dont_bother_trying_to_add_the_rest_of_pics = True
        #if dont_bother_trying_to_add_the_rest_of_likes:
            #print("Como ya he detectado unos likes insertados, y van por orden, ya no intento insertar más, porque el resto ya estarán.")
        #    pass
        #else:  
        #if update['_shards']['successful'] == 0:
        #    print("Algo ha pasado y no he podido actualizar los likes")
            days=0
            index_daily=(date.today()-timedelta(days=days)).strftime("%Y%m%d")
            if es.search(index="picsdaily-*", doc_type='likes', q="_id:"+pic_id, size=0)['hits']['total'] == 0:
                result = es.index(index='picsdaily-' +index_daily,doc_type='likes', id=pic_id,body={'number':likes, 'timestamp': timestamp_daily})
            else: 
                while not es.exists(index="picsdaily-"+index_daily, doc_type='likes', id=pic_id):
                    timestamp_daily = (date.today()-timedelta(days=days)).strftime("%s")+"000"
                    print("Dias = "+str(days)+" . Le pongo " + str(likes) + " likes a la foto " + str(pic_id))
                    result = es.index(index='picsdaily-' +index_daily,doc_type='likes', id=pic_id,body={'number':likes, 'timestamp': timestamp_daily})
                    days+=1
                    index_daily=(date.today()-timedelta(days=days)).strftime("%Y%m%d")


#            likes_diff={}
#            oldvalue=likes
#            oldest_index_found = False
#            for diff_days in [1,3,7,30,90,180,365]:
#                compared_date=date.today()-timedelta(days=diff_days)
#                suffix=compared_date.strftime("%Y%m%d")
#                if not oldest_index_found:
#                    if es.exists('picsdaily-'+suffix, doc_type='likes', id=pic_id):
#                        oldvalue = es.get(index='picsdaily-'+suffix, doc_type='likes', id=pic_id)['_source']['number']
#                    else:
#                        oldest_index_found = True
#                likes_diff[diff_days] = likes - oldvalue
        #    print("Followers" + str(followers_diff) + " y follows " +str(following_diff))
            #es.index(index='pics', doc_type="likes_diffs", id=pic_id, body=likes_diff)
#            print("es.index(index='pics', doc_type='likes_diffs', id="+pic_id+", body="+str(likes_diff)+")")
#        else:
#            print("Skipping that shit")
#    print(json.dumps(data, indent=4))
    update_counters(es, iguser)
create_snapshot(es)
update_index_aliases(es)
