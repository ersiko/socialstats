import sys
import configparser
import os
import json
import igscrape
import elasticsearch
from datetime import date, timedelta

config = configparser.ConfigParser()
scriptdir= os.path.dirname(sys.argv[0])
if scriptdir == "":
    scriptdir = os.getcwd()
conffile = scriptdir + '/socialstats.config'
config.read(conffile)


es = elasticsearch.Elasticsearch(['10.8.0.1'])

res=es.search(index='igusers',doc_type='users')

rest_already_indexed = False
index_suffix=date.today().strftime("%Y%m%d")
 
for iguser in res['hits']['hits']:
    data, maxid = igscrape.get_iguser_data(iguser['_id'])
    igusername = iguser['_id']
    followers = data['entry_data']['ProfilePage'][0]['user']['followed_by']['count']
    following = data['entry_data']['ProfilePage'][0]['user']['follows']['count']

    following_diff={}
    followers_diff={}
    es.index(index='userdaily-' +index_suffix,doc_type='follows', id=igusername,body={'followers':followers, 'following': following})
    for diff_days in [1,3,7,30,90,180,365]:
        compared_date=date.today()-timedelta(days=diff_days)
        suffix=compared_date.strftime("%Y%m%d")
        if es.exists(index='userdaily-'+suffix, doc_type='follows', id=igusername):
            oldvalue = es.get(index='userdaily-'+suffix, doc_type='follows', id=igusername)
            following_diff[diff_days] = following - oldvalue['_source']['following']
            followers_diff[diff_days] = followers - oldvalue['_source']['followers']
        else: 
#            print("No existe el indice " + str(diff_days))
            break
#    print("Followers" + str(followers_diff) + " y follows " +str(following_diff))
    es.index(index='igusers', doc_type="followers_diffs", id=igusername, body=followers_diff)
    es.index(index='igusers', doc_type="following_diffs", id=igusername, body=following_diff)
#    print(igusername + " followed by " + str(followers) + " and following " + str(following))
    for pic in data['entry_data']['ProfilePage'][0]['user']['media']['nodes']:
        pic_id = pic['code']
        likes = pic['likes']['count']
        if not es.exists(index="pics", doc_type="pics", id=pic_id):
            dateposted = pic['date']
            thumbnail = pic['thumbnail_src']
            fullpic = pic['display_src']
            caption = pic['caption']
            print("Username " + igusername + " posted pic "+ pic_id + " on " + str(dateposted) + 
              " and it has " + str(likes) + " likes. You can see a thumbnail at " + thumbnail + 
              " and the full pic at " + fullpic + ". The caption is " + caption)
            pic_object = {'username': igusername, 'dateposted': dateposted, 'thumbnail': thumbnail, 'fullpic' : fullpic, 'caption': caption}
            es.index(index='pics', doc_type='pics', id=pic_id, body=pic_object)
        else:
            print("La foto " + pic_id + " ya está en elasticsearch")
        if rest_already_indexed == False:
            result = es.index(index='picsdaily-' +index_suffix,doc_type='likes', id=pic_id,body={'number':likes})
#            if result['created'] == False:
#                rest_already_indexed = True
            likes_diff={}
            for diff_days in [1,3,7,30,90,180,365]:
                compared_date=date.today()-timedelta(days=diff_days)
                suffix=compared_date.strftime("%Y%m%d")
                if es.exists('picsdaily-'+suffix, doc_type='likes', id=pic_id):
                    oldvalue = es.get(index='picsdaily-'+suffix, doc_type='likes', id=pic_id)
                    likes_diff[diff_days] = likes - oldvalue['_source']['number']
                else: 
                    print("No existe el indice " + str(diff_days))
                    break
        #    print("Followers" + str(followers_diff) + " y follows " +str(following_diff))
            es.index(index='pics', doc_type="likes_diffs", id=pic_id, body=likes_diff)
        else:
            print("Skipping that shit")
#    print(json.dumps(data, indent=4))