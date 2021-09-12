import requests
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import ast
import json
import uuid
import os.path
import urllib.parse
import sys
from time import time

API_URL = 'https://api.boosty.to'

class BoostyToRSS():
  def __init__(self, config_path='config.json'):
    self.config_path = config_path

    if os.path.isfile(self.config_path):
      with open(self.config_path, 'r') as config_file:
        self.config = json.load(config_file)
    else:
      self.config = {}
    
    if 'uuid' in self.config:
      self.uuid = self.config['uuid']
    else:
      self.uuid = str(uuid.uuid1())

    if 'phone_number' in self.config:
      self.phone_number = self.config['phone_number']
    else:
      self.phone_number = urllib.parse.quote_plus(input("Enter your phone number: "))

    if 'access_token' in self.config:
      self.access_token = self.config['access_token']
      self.refresh_token = self.config['refresh_token']
      if 'expires' in self.config:
        self.expires = self.config['expires']
        if int(time()) >= self.expires:
          refresh_needed = True
      else:
        refresh_needed = True
    else:
      self.authenticate()

    if refresh_needed:
      self.refresh_auth()

  def __del__(self):
    print('Destructor called, vehicle deleted.')

  def save_config(self):
    with open(self.config_path, 'w') as config_file:
      self.config['uuid'] = self.uuid
      self.config['phone_number'] = self.phone_number
      self.config['access_token'] = self.access_token
      self.config['refresh_token'] = self.refresh_token
      self.config['expires'] = self.expires
      json.dump(self.config, config_file)
  
  def authenticate(self):
    request_body = f'client_id={self.phone_number}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-From-Id': self.uuid,
        'X-App': 'web',
        'X-Referer': '', 
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        }

    response = requests.post(f'{API_URL}/oauth/phone/authorize',
        data=request_body,
        headers=headers)

    response_data = response.json()
    code = response_data['code']
    sms_code = input("SMS Code: ")

    request_body = f'device_id={self.uuid}&sms_code={sms_code}&device_os=web&client_id={self.phone_number}&code={code}'

    response = requests.post(f'{API_URL}/oauth/phone/token',
        data=request_body,
        headers=headers)

    response_data = response.json()
    self.refresh_token = response_data['refresh_token']
    self.access_token = response_data['access_token']
    self.expires = int(time()) + response_data['expires_in']

    self.save_config()


  def refresh_auth(self):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0',
        'Authorization': f'Bearer {self.access_token}',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-From-Id': self.uuid,
        'X-App': 'web',
        'X-Referer': '', 
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        }
    request_body = f'device_id={self.uuid}&device_os=web&grant_type=refresh_token&refresh_token={self.refresh_token}'
    response = requests.post(f'{API_URL}/oauth/token/',
        data=request_body,
        headers=headers)

    response_data = response.json()
    self.refresh_token = response_data['refresh_token']
    self.access_token = response_data['access_token']
    self.expires = int(time()) + response_data['expires_in']

    self.save_config()

  def generate_rss(self, author):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0',
        'Authorization': f'Bearer {self.access_token}',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-From-Id': self.uuid,
        'X-App': 'web',
        'X-Referer': '', 
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        }

    # TODO: check for authentication errors
    response = requests.get(f'{API_URL}/v1/blog/{author}',
        headers=headers)
    response_data = response.json()
    if response_data['owner']['hasAvatar']:
      logo_url = response_data['owner']['avatarUrl']
    title = response_data['owner']['name']

    podcast_desc = ''
    for block in response_data['description']:
      if 'modificator' in block and block['modificator'] != 'BLOCK_END' and block['type'] == 'text':
          text = ast.literal_eval(block['content'])
          podcast_desc += text[0] + '\r\n'

    
    response = requests.get(f'{API_URL}/v1/blog/{author}/post/',
        headers=headers)

    response_data = response.json()

    fg = FeedGenerator()
    fg.load_extension('podcast')
    fg.link(href=f'https://boosty.to/{author}', rel='self')
    fg.title(title)
    fg.description(podcast_desc)
    fg.image(url=logo_url)

    # TODO: move from feedgen, it's very unflexible
    for post in response_data['data']:
        if not post['hasAccess']:
            continue
        desc = ''
        for content in post['data']:
            if content['type'] == 'audio_file':
                url = content['url']
                params = post['signedQuery']
                download_url = f'{url}{params}'
            if 'modificator' in content and content['modificator'] != 'BLOCK_END' and content['type'] == 'text':
                text = ast.literal_eval(content['content'])
                desc += text[0] + '\r\n'

        # TODO: add post covers
        fe = fg.add_entry()
        
        for teaser in post['teaser']:
            if 'url' in teaser:
                post_logo = teaser['url']
                fe.enclosure(post_logo, 0, 'image/jpeg')
        # TODO: get real timezone
        fe.pubDate(datetime.fromtimestamp(post['publishTime'], timezone.utc))
        fe.title(post['title'])
        fe.description(desc)
        fe.enclosure(download_url, 0, 'audio/mpeg')

    fg.rss_str(pretty=True)
    fg.rss_file(f'{author}.xml')

if __name__ == "__main__":
  # TODO: add cli arguments handling
  b = BoostyToRSS()
  b.generate_rss(sys.argv[1])
