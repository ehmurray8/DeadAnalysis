import os
import json
import http.client
import pickle
import urllib.parse as urlp
from api_key import API_KEY
from config import ARTISTS, SELECTED_COVERS
import song


HEADERS = {
    'x-api-key': API_KEY,
    'accept': "application/json",
    'cache-control': "no-cache",
    'postman-token': "44195584-3280-9850-105d-87b18ab76395"
}

def get_song_data():
    music = song.MusicData()
    conn = http.client.HTTPSConnection("api.setlist.fm")
    for artist in ARTISTS:
        print(artist)
        total = 2
        i = 1
        while i <= total:
            url_artist = urlp.quote_plus(artist)
            pickle_artist = artist.replace(" ", "_")
            print("Page {}".format(i))
            conn.request("GET", "/rest/1.0/search/setlists?artistName={}&p={}"
                        .format(url_artist, i), headers=HEADERS)
            res = conn.getresponse()
            data = res.read()
            main_data = json.loads(data.decode("utf-8"))
            setlists = main_data["setlist"]
            total = float(main_data["total"])
            items = float(main_data["itemsPerPage"])
            total /= items
            total = int(total + .5)
            for slist in setlists:
                venue = slist["venue"]
                date = slist["eventDate"]
                tour = "N/A"
                if "tour" in slist:
                    tour = slist["tour"]["name"]
                state = "N/A"
                if "state" in venue["city"]:
                    state = venue["city"]["state"]

                loc = song.Location(venue["city"]["name"], state, venue["city"]["country"]["name"], 
                                    venue["name"], venue["city"]["coords"])

                for music_set in slist["sets"]["set"]:
                    for sng in music_set["song"]:
                        orig_art = artist
                        if "cover" in sng:
                            orig_art = sng["cover"]["name"]
                        song_obj = song.Song(loc, date, tour, artist, orig_art, sng["name"])
                        music.add_song(song_obj)
            i+=1

    with open(os.path.join("pickle_data", "all_song_data.pickle"), "wb") as f:
        pickle.dump(music, f)


def get_pickled_song_data():
    with open(os.path.join("pickle_data", "all_song_data.pickle"), "rb") as f:
        music = pickle.load(f)
    return music