import os
import sys
import json
import zipfile
import requests
import filecmp
import shutil
import errno
import re

VERSIONS_JSON = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

def fetch_json(url):
    response = requests.get(url)
    return response.json()

def get_urls(type, number):
    global VERSIONS_JSON
    urls = {}

    for item in fetch_json(VERSIONS_JSON)['versions']:
        if len(urls) < (number + 1):
            if item['type'] == type:
                if len(urls.keys()) == 0:
                    urls[item['id']] = item['url']
                else:
                    if type == 'release':
                        latest = list(urls.keys())[-1].split('.')[1]
                        current = item['id'].split('.')[1]
                        if current != latest:
                            urls[item['id']] = item['url']
                    else: urls[item['id']] = item['url']
    
    return urls.values()

def save_temp(urls, type):
    names = []
    if not os.path.exists('temp'):
        os.mkdir('temp')
    
    for url in urls:
        if type == 'release':
            name = '1.' + fetch_json(url)['id'].split('.')[1]
        else:
            name = fetch_json(url)['id']
        names.append(name)
        
        os.mkdir('temp/' + name)
        with open('temp/' + name + '.zip', 'wb') as f:
            f.write(requests.get(fetch_json(url)['downloads']['client']['url']).content)
        
        zip_ref = zipfile.ZipFile('temp/' + name + '.zip', 'r')
        zip_ref.extractall('temp/' + name)
        zip_ref.close()
    
    return names

def diff_folders(new, old, type, delFolder = False):
    added =[]
    changed = []
    deleted = []
    
    if (delFolder == False):
        diff_folders(old, new, type, True)

    for root, dirs, files in os.walk('temp/' + new):
        for name in files:
            src = os.path.join(root, name)
            need_check = src.startswith('temp/' + new + "/assets/minecraft/textures/")
            
            if need_check:
                dest = src.replace(new, old, 1)
                
                if (delFolder == False):
                    if not os.path.exists(dest):
                        added.append(src)
                    elif not filecmp.cmp(src, dest):
                        changed.append(src)
                else:
                    if not os.path.exists(dest):
                        deleted.append(src)
    
    for item in added:
        save_diff(new, "../deploy/" + type.capitalize() + "s/" + new + "/added", item)
    
    for item in changed:
        save_diff(new, "../deploy/" + type.capitalize() + "s/" + new + "/changed", item)
    
    for item in deleted:
        save_diff(new, "../deploy/" + type.capitalize() + "s/" + old + "/deleted", item)

def save_diff(base_folder, new_folder, item):
    src = item
    dest = item.replace(base_folder + "/assets/minecraft/textures/", new_folder + "/")
    
    try:
        shutil.copy(src, dest)
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise
        
        os.makedirs(os.path.dirname(dest))
        shutil.copy(src, dest)

def main():
    type = sys.argv[1]
    number = int(sys.argv[2])

    urls = get_urls(type, number)
    folders = save_temp(urls, type)

    for x in range(number):
        diff_folders(folders[x], folders[x + 1], type)

if __name__ == '__main__':
    main()