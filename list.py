import requests
from bs4 import BeautifulSoup as bs
import json

r = requests.get('https://www.instagram.com/alquintopino/')
p = bs(r.content,"html.parser")
for script in p.find_all('script'):
    if 'window._sharedData' in script.text:
        data=json.loads(script.text[20:-1])

for pic in data['entry_data']['ProfilePage'][0]['user']['media']['nodes']:
    print(''.join(pic['caption'][:25].splitlines()) + ": " + str(pic['likes']['count']))
  