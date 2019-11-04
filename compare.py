import os
import sys
import json
import zipfile
import requests
import filecmp
import shutil
import errno

VERSIONS_JSON = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

def fetchJson(url):
	response = requests.get(url)
	return response.json()

def getURLs(type, number):
    global VERSIONS_JSON
    urls = []

    for item in fetchJson(VERSIONS_JSON)['versions']:
        if len(urls) < (number + 1):
            if item['type'] == type:
                urls.append(item['url'])
    
    return urls

def saveTemp(urls):
	names = []
	if not os.path.exists('temp'):
		os.mkdir('temp')
	
	for url in urls:
		name = fetchJson(url)['id']
		names.append(name)
		
		os.mkdir('temp/' + name)
		with open('temp/' + name + '.zip', 'wb') as f:
			f.write(requests.get(fetchJson(url)['downloads']['client']['url']).content)
		
		zip_ref = zipfile.ZipFile('temp/' + name + '.zip', 'r')
		zip_ref.extractall('temp/' + name)
		zip_ref.close()
	
	return names

def diffFolders(new, old, type, delFolder = False):
	added =[]
	changed = []
	deleted = []
	
	if (delFolder == False):
		diffFolders(old, new, type, True)

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
		saveDiff(new, "../deploy/" + type.capitalize() + "s/" + new + "/added", item)
	
	for item in changed:
		saveDiff(new, "../deploy/" + type.capitalize() + "s/" + new + "/changed", item)
	
	for item in deleted:
		saveDiff(new, "../deploy/" + type.capitalize() + "s/" + old + "/deleted", item)

def saveDiff(base_folder, new_folder, item):
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

    urls = getURLs(type, number)
    folders = saveTemp(urls)

    for x in range(number):
        diffFolders(folders[x], folders[x + 1], type)

if __name__ == '__main__':
	main()