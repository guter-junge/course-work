import requests
from datetime import datetime
import json
import time
from tqdm import tqdm

vk_token = 'vk_token'
ya_token = input('Введите токен с полигона Я.диска: ')
version = '5.131'
owner_id = int(input('Введите id пользователя: '))
disk_folder = '/Vk_photos/'

class VkUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version):
        self.params = {
            'access_token': token,
            'v': version
        }

    def get_photos(self, owner_id):
        get_photos_url = self.url + 'photos.get'
        get_photos_params = {
            'owner_id': owner_id,
            'album_id': 'profile',
            'extended': 1,
            'feed_type': 'photo'
        }
        response = requests.get(get_photos_url, params={**self.params, **get_photos_params}).json()
        return response

    def get_photos_likes_count(self, owner_id):
        response = self.get_photos(owner_id)
        count = [item['likes']['count'] for item in response['response']['items']]
        return count

    def get_photo_upload_date(self, owner_id):
        response = self.get_photos(owner_id)
        initial_date = [item['date'] for item in response['response']['items']]
        date_formatted = []
        for date in initial_date:
            date_formatted.append(datetime.fromtimestamp(date).strftime('%Y-%m-%d'))
        return date_formatted

    def get_max_size_photo(self, owner_id):
        response = self.get_photos(owner_id)
        max_size_urls = []
        photos = [item['sizes'] for item in response['response']['items']]
        for photo in photos:
            max_size_urls.append(photo[-1]['url'])
        return max_size_urls

    def get_photo_data(self, owner_id):
        response = self.get_photos(owner_id)
        likes_count = self.get_photos_likes_count(owner_id)
        upload_date = self.get_photo_upload_date(owner_id)
        photo_urls = self.get_max_size_photo(owner_id)
        photo_all_sizes = [item['sizes'] for item in response['response']['items']]
        max_size_type = []
        for photo in photo_all_sizes:
            max_size_type.append(photo[-1]['type'])
        photo_info = {upload_date[i]: [likes_count[i], max_size_type[i], photo_urls[i]] for i in range(len(likes_count))}
        photo_data = []
        likes_list = []
        final = []
        for upload_date, value in photo_info.items():
            sub_json = {}
            if value[0] not in likes_list:
                likes_list.append(value[0])
                file_name = f'{value[0]}.jpeg'
                size = f'{value[1]}'
                sub_json['file_name'] = file_name
                sub_json['size'] = size
                final.append(sub_json)
            else:
                file_name = f'{value[0]} {upload_date}.jpeg'
                size = f'{value[1]}'
                sub_json['file_name'] = file_name
                sub_json['size'] = size
                final.append(sub_json)
            photo_data.append({'file_name': file_name, 'url': f'{value[2]}'})
        with open('final_json.json', 'w') as final_json:
            json.dump(final, final_json, indent=4)
        return photo_data


class Ya_disk:
    url = 'https://cloud-api.yandex.net/v1/disk/resources/'

    def __init__(self, token, disk_folder):
        self.token = token
        self.disk_folder = disk_folder

    def get_headers(self):
        return {
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def upload_file_to_disk(self, file_name, url):
        upload_url = self.url + 'upload'
        headers = self.get_headers()
        params = {'url': url, 'path': f'{self.disk_folder}{file_name}'}
        response = requests.post(upload_url, headers=headers, params=params)
        response.raise_for_status()
        if response.status_code == 202:
            print("Success")
        else:
            print('Failed to upload files')


if __name__ == '__main__':
    vk = VkUser(token=vk_token, version=version)
    ya = Ya_disk(token=ya_token, disk_folder=disk_folder)
    photo_data = vk.get_photo_data(owner_id)

    for data in tqdm(photo_data):
        response = requests.get(data['url'])
        response.raise_for_status()
        ya.upload_file_to_disk(data['file_name'], data['url'])
        time.sleep(1)