import requests
from bs4 import BeautifulSoup as bs
import json
import time

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
                    page_info = data['entry_data']['ProfilePage'][0]['user']['media']['page_info']
                else:
                    data2 = json.loads(script.text[20:-1])
                    data['entry_data']['ProfilePage'][0]['user']['media']['nodes'] += data2['entry_data']['ProfilePage'][0]['user']['media']['nodes']
                    page_info = data2['entry_data']['ProfilePage'][0]['user']['media']['page_info']          
        if data['entry_data']['ProfilePage'][0]['user']['media']['page_info']['has_next_page'] == True:
            max_id = "?max_id=" +page_info['end_cursor']
            cursor+=1
        else:
            break
        print(str(cursor), end=" ", flush=True)
        time.sleep(1)
    return data , max_id

if __name__ == "__main__":
    import sys
    print(json.dumps(get_iguser_data(sys.argv[1], int(sys.argv[2]))))