import os
import json
import http.client
import pickle
import urllib.parse as urlp
from api_key import API_KEY
from config import ARTIST
from music import MusicData
from song import Venue, Tour, Concert, Song, Set


HEADERS = {
    'x-api-key': API_KEY,
    'accept': "application/json",
    'cache-control': "no-cache",
}

def get_song_data():
    music = MusicData()
    conn = http.client.HTTPSConnection("api.setlist.fm")
    census_conn = http.client.HTTPSConnection("geo.fcc.gov")
    conn.connect()
    census_conn.connect()
    total = 2
    i = 1
    while i <= total:
        url_artist = urlp.quote_plus(ARTIST)
        print("Page {}".format(i))
        conn.request("GET", "/rest/1.0/search/setlists?artistName={}&p={}" .format(url_artist, i), headers=HEADERS)
        res = conn.getresponse()
        data = res.read()
        main_data = json.loads(data.decode("utf-8"))
        setlists = main_data["setlist"]
        total = float(main_data["total"])
        items = float(main_data["itemsPerPage"])
        total /= items
        total = int(total + .5)
        for setlist in setlists:
            venue = setlist["venue"]
            date = setlist["eventDate"]
            tour = None
            if "tour" in setlist:
                tour = setlist["tour"]["name"]
            state = "NA"
            state_code = "NA"
            city = venue["city"]
            if "state" in city:
                state = city["state"]
            if "stateCode" in city:
                state_code = city["stateCode"]
            coordinates = city["coords"]
            fips = get_fips(census_conn, coordinates)
            venue_id = venue["id"]
            country = city["country"]
            if venue_id not in music.venues:
                try:
                    lat, long = coordinates["lat"], coordinates["long"]
                except KeyError:
                    lat, long = -1, -1
                venue_obj = Venue(venue["name"], city["name"], state, state_code, country["name"],
                                  country["code"], lat, long, fips)
                music.venues[venue_id] = venue_obj
            if tour is not None and tour not in [tour.name for tour in music.tours]:
                tour = Tour(tour)
                music.tours.append(tour)
            elif tour is not None:
                tour = [t for t in music.tours if t.name == tour][0]

            sets = []
            encores = []
            for s in setlist["sets"]["set"]:
                songs = []
                for song in s["song"]:
                    if "cover" in song:
                        orig_artist = song["cover"]["name"]
                    else:
                        orig_artist = ARTIST
                    if song["name"] not in music.songs:
                        song = Song(ARTIST, orig_artist, song["name"])
                        music.songs[song.name] = song
                    else:
                        song = music.songs[song["name"]]
                    if "encore" in s:
                        encores.append(song)
                    else:
                        songs.append(song)
                if "encore" not in s:
                    sets.append(Set(songs))

            encores = Set(encores)
            concert = Concert(date, venue_id, sets, encores, tour)
            music.concerts.append(concert)
        i+=1

    with open(os.path.join("pickle_data", "{}_song_data.pickle".format(ARTIST)), "wb") as f:
        pickle.dump(music, f)


def get_fips(census_conn, coords) -> str:
    try:
        census_conn.request("GET", "/api/census/area?lat={}&lon={}&format=json".format(coords["lat"], coords["long"]))
        response = census_conn.getresponse().read()
        response_json = json.loads(response.decode("utf-8"))
        try:
            fips = response_json["results"][0]["county_fips"]
        except (IndexError, AttributeError):  # Non-US Concert
            fips = "NA"
        return fips
    except KeyError:
        return "NA"


def get_pickled_song_data() -> MusicData:
    with open(os.path.join("pickle_data", "{}_song_data.pickle".format(ARTIST)), "rb") as f:
        music = pickle.load(f)  # type: MusicData
    return music
