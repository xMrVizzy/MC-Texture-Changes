import os
import json
import requests
import zipfile
import filecmp
import shutil
import errno

VERSIONS_JSON = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
LATEST_VERSION = 0

def fetch_json(url):
	response = requests.get(url)
	return response.json()

def save_temp(urls):
	names = []
	if not os.path.exists('temp'):
		os.mkdir('temp')
	
	for url in urls:
		name = fetch_json(url)['id']
		names.append(name)
		
		os.mkdir('temp/' + name)
		with open('temp/' + name + '.zip', 'wb') as f:
			f.write(requests.get(fetch_json(url)['downloads']['client']['url']).content)
		
		zip_ref = zipfile.ZipFile('temp/' + name + '.zip', 'r')
		zip_ref.extractall('temp/' + name)
		zip_ref.close()
	
	return names

def diff_folders(latest, previous, delFolder = False):
	added =[]
	changed = []
	deleted = []
	
	if (delFolder == False):
		diff_folders(previous, latest, True)

	for root, dirs, files in os.walk('temp/' + latest):
		for name in files:
			src = os.path.join(root, name)
			need_check = src.startswith('temp/' + latest + "/assets/minecraft/textures/")
			
			if need_check:
				dest = src.replace(latest, previous, 1)
				
				if (delFolder == False):
					if not os.path.exists(dest):
						added.append(src)
					elif not filecmp.cmp(src, dest):
						changed.append(src)
				else:
					if not os.path.exists(dest):
						deleted.append(src)
	
	for item in added:
		save_diff(latest, "../deploy/" + latest +"/added", item)
	
	for item in changed:
		save_diff(latest, "../deploy/" + latest +"/changed", item)
	
	for item in deleted:
		save_diff(latest, "../deploy/" + previous +"/deleted", item)

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
	versions_url = [x['url'] for x in fetch_json(VERSIONS_JSON)['versions'][LATEST_VERSION:LATEST_VERSION + 2]]
	folders = save_temp(versions_url)
	
	diff_folders(folders[0], folders[1])

if __name__ == '__main__':
	main()
