import os
import json
import http.client
import pickle
import urllib.parse as urlp
import calendar
from datetime import datetime
from api_key import API_KEY

conn = http.client.HTTPSConnection("api.setlist.fm")

headers = {
    'x-api-key': API_KEY,
    'accept': "application/json",
    'cache-control': "no-cache",
    'postman-token': "44195584-3280-9850-105d-87b18ab76395"
}

def get_song_data(artist):
    songs = FreqDict()
    covers = FreqDict()
    total = 2
    i = 1
    print(artist)
    pickle_artist = None
    while i <= total:
        url_artist = urlp.quote_plus(artist)
        pickle_artist = artist.replace(" ", "_")
        print("Page {}".format(i))
        conn.request("GET", "/rest/1.0/search/setlists?artistName={}&p={}"
                    .format(url_artist, i), headers=headers)
        res = conn.getresponse()
        data = res.read()
        main_data = json.loads(data.decode("utf-8"))
        setlists = main_data["setlist"]
        total = float(main_data["total"])
        items = float(main_data["itemsPerPage"])
        total /= items
        total = int(total + .5)
        for slist in setlists:
            for music_set in slist["sets"]["set"]:
                for song in music_set["song"]:
                    songs.add(song["name"])
                    if "cover" in song:
                        covers.add((song["cover"]["name"], song["name"]))
        i+=1

    if pickle_artist is not None:
        with open(os.path.join("pickle_data", "{}_songs.pickle".format(pickle_artist)), "wb") as f:
            pickle.dump(songs, f)

        with open(os.path.join("pickle_data", "{}_covers.pickle".format(pickle_artist)), "wb") as f:
            pickle.dump(covers, f)

def get_pickled_songs(artist, songs_list, covers_list):
    pickle_artist = artist.replace(" ", "_")
    with open(os.path.join("pickle_data", "{}_songs.pickle".format(pickle_artist)), 
            "rb") as f:
        songs_list.append(pickle.load(f))

    with open(os.path.join("pickle_data", "{}_covers.pickle".format(pickle_artist)),
            "rb") as f:
        covers_list.append(pickle.load(f))

class Location():
    def __init__(self, city, state, country, venue, coords):
        self.city = city
        self.state = state
        self.country = country
        self.venue = venue
        self.latitude = coords["lat"]
        self.longitude = coords["long"]
    

class Song():
    def __init__(self, loc, date, artist, name):
        self.location = loc
        self.date = datetime.strptime(date, "%d-%m-%Y").date()
        self.artist = artist
        self.name = name

    def get_weekday(self):
        return calendar.day_name[self.date.weekday()]


class FreqDict():
    def __init__(self):
        self.dictionary = {}

    def add(self, key):
        if key in self.dictionary:
            old_val = self.dictionary[key]
            self.dictionary[key] = old_val + 1
        else:
            self.dictionary[key] = 1

    def sorted_list(self):
        return [(key, self.dictionary[key]) for key in sorted(self.dictionary, key=self.dictionary.get, reverse=True)]

    def keys_set(self):
        return set(self.dictionary.keys())

    def __str__(self):
        return str(self.dictionary)

    def __len__(self):
        return len(self.dictionary)

    def __repr__(self):
        return str(self.dictionary)


if __name__ == "__main__":
    artists = ["Grateful Dead", "Ratdog", "Dead & Company", "Jerry Garcia Band", "Phil and Friends", "Furthur", "The Other Ones"]
    #artists = ["Grateful Dead"]
    cover_artists = ["Bob Dylan", "The Beatles", "The Rolling Stones", "Creedence Clearwater Revival", "The Who"]
    songs_list = []
    covers_list = []
    for artist in artists:
        #get_song_data(artist)
        get_pickled_songs(artist, songs_list, covers_list)

    for songs, covers, artist in zip(songs_list, covers_list, artists):
        print(artist)
        print(songs.sorted_list())
        print("Number of unique songs: {}".format(len(songs)))

        print("\nCovered songs")
        print(covers.sorted_list())
        print("Number of covered songs: {}".format(len(covers)))
        print("\n")

    all_songs = [sl.keys_set() for sl in songs_list]
    all_covers = [cl.keys_set() for cl in covers_list]

    print("All songs")
    
    print(set.union(*all_songs))
    print("Number of unique songs played by all bands: {}".format(len(set.union(*all_songs))))
    
    print("\nAll covers")
    print(set.union(*all_covers))
    print("Number of unique covered songs by all bands: {}".format(len(set.union(*all_covers))))

    print("\nCommon songs")
    print(set.intersection(*all_songs))
    print("Number of songs played by all bands: {}".format(len(set.intersection(*all_songs))))

    print("\nCommon covers")
    print(set.intersection(*all_covers))
    print("Number of songs covered by all bands: {}".format(len(set.intersection(*all_songs))))

    covered = FreqDict()
    for covers in all_covers:
        for cover in covers:
            covered.add(cover[1])

     
    print("\n Covered artists")
    print(covered.sorted_list())
    print("Number of covered artists: {}\n".format(len(covered.sorted_list())))

    chosen_covers = [set() for _ in range(len(cover_artists))]
    for artist, cc in zip(cover_artists, chosen_covers):
        for covers in all_covers:
            for cover in covers:
                if cover[1] == artist:
                    cc.add(cover[0])
        print("Songs covered by: {}".format(artist))
        print(cc)
        print("Number of {} songs covered: {}\n".format(artist, len(cc)))
