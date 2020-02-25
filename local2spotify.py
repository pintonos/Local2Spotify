import os
import sys
import spotipy
import spotipy.util as util
from pprint import pprint
import json
import re
from string import digits

with open('config.json') as f:
    config = json.load(f)

path = config['search_path']

fileNotFoundPath = "notFound.txt"

scope = 'playlist-modify-public'

def getListOfFiles():
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            if '.mp3' in file or '.m4a' in file:
                files.append(file)
    return files

def cleanFilenames(files):
    clean_filenames = []
    for file in files:
        file = file.replace('.mp3', '')
        file = file.replace('.m4a', '')
        file = file.replace('.', '')
        file = file.replace('_', ' ')
        if 'Remix' not in file or 'Edit' not in file:
            file = re.sub('\(.*?\)', '', file)
            file = re.sub('\[.*?\]', '', file)
            file = re.sub('\{.*?\}', '', file)
        else:
            file = file.replace('(', '')
            file = file.replace(')', ' ')
            file = file.replace('[', '')
            file = file.replace(']', ' ')
        #file = file.translate({ord(k): None for k in digits})
        file = re.sub('\d\d*? ', '', file) # songs starting with their number on an album
        file = re.sub('\d\d*?-', '', file)
        file = file.strip()
        clean_filenames.append(file)

    return clean_filenames

files = getListOfFiles()
cleanedFilenames = cleanFilenames(files)

if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    print("Usage: %s username" % (sys.argv[0],))
    sys.exit()


token = util.prompt_for_user_token(username,
                           scope,
                           client_id=config['client_id'],  
                           client_secret=config['client_secret'],
                           redirect_uri='http://localhost/')

if token:
    sp = spotipy.Spotify(auth=token)
    sp.trace = False
    playlist = sp.user_playlist_create(username, 'local2spotify',
                                        description='local2spotify found songs on Spotify.')

    #search for all tracknames
    track_ids = []
    fileNotFound = open(fileNotFoundPath,"w+")
    for file in cleanedFilenames:
        result = sp.search(file, type="track", limit=1)
        if result['tracks']['items']:
            print("found: ", file)
            track_ids.append(result['tracks']['items'][0]['id'])
        else:
            print("not found: ", file)
            try:
                fileNotFound.write(file + "\n")
            except:
                print("error writing song name to file")

        if len(track_ids) is 99:
            # add tracks to playlist
            results = sp.user_playlist_add_tracks(username, playlist['id'], track_ids) # can add maxium 100 tracks per request
            track_ids = []

    # final add tracks to playlist
    results = sp.user_playlist_add_tracks(username, playlist['id'], track_ids)

    fileNotFound.close()

else:
    print("Can't get token for", username)

