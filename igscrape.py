import requests
from bs4 import BeautifulSoup as bs
import json

def get_iguser_data(iguser, max_cursor=1, max_id=""):
    cursor=0
    data = {}
    while cursor < max_cursor:
        r = requests.get('https://www.instagram.com/'+ iguser +'/'+max_id)
        p = bs(r.content,"html.parser")
        for script in p.find_all('script'):
            if 'window._sharedData' in script.text:
                if cursor == 0:
                    data = json.loads(script.text[20:-1])
                else:
                    data['entry_data']['ProfilePage'][0]['user']['media']['nodes'].append(json.loads(script.text[20:-1])['entry_data']['ProfilePage'][0]['user']['media']['nodes'])
        if data['entry_data']['ProfilePage'][0]['user']['media']['page_info']['has_next_page'] == True:
            max_id = "?max_id=" +data['entry_data']['ProfilePage'][0]['user']['media']['page_info']['end_cursor']
            cursor+=1
        else:
            break
    return data , max_id

if __name__ == "__main__":
    import sys
    print(json.dumps(get_iguser_data(sys.argv[1], int(sys.argv[2]))))