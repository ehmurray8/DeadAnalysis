import json
import http.client
import datetime
import urllib.parse as urlp
from django.conf import settings
from .models import Song, Set, Concert, Venue, Tour, Artist, SetlistFMStatus
from musicanalysis.celery import app
import logging
import socket
import threading
import queue
import time
import musicbrainzngs as mb
from musicanalysis._keys import MB_UNAME, MB_PASSWORD

logger = logging.getLogger(__name__)

HEADERS = {
    'x-api-key': settings.SETLIST_FM_API_KEY,
    'accept': "application/json",
}


def setup_status(artist):
    artist_name = urlp.unquote(artist, encoding="utf-8")
    try:
        artist_obj = Artist.objects.get(name__iexact=artist_name)
    except Artist.DoesNotExist:
        artist_obj = Artist(name=artist_name)
        artist_obj.save()
    try:
        status = SetlistFMStatus.objects.get(artist__name__iexact=artist_obj.name)
        status.finished = False
        status.published = None
        status.started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status.save()
    except (IndexError, SetlistFMStatus.DoesNotExist):
        status = SetlistFMStatus()
        status.save()
        artist_obj.setlistfmstatus_set.clear()
        artist_obj.save()
        artist_obj.setlistfmstatus_set.add(status)
        artist_obj.save()
    return artist_obj, status


def handle_parsing(q: queue.Queue):
    while True:
        try:
            setlists, artist, curr, total, status = q.get()
            print("Got first item")
            parse_setlists(setlists, artist, curr)
            status.current_page = curr
            status.final_page = total
            status.save()
            if curr == total:
                break
        except queue.Empty:
            print("Not found")
            time.sleep(.05)


@app.task
def get_song_data(artist):
    total = 2
    i = 1
    artist, status = setup_status(artist)
    mb_id = None
    setlist_queue = queue.Queue()
    threading.Thread(target=handle_parsing, args=(setlist_queue,)).start()
    while i <= total:
        response = ""
        while not response:
            try:
                conn = http.client.HTTPSConnection("api.setlist.fm")
                conn.connect()
                logger.info("{} Page {}".format(artist.name, i))
                if mb_id is None:
                    conn.request("GET", "/rest/1.0/search/setlists?artistName={}&p={}"
                                 .format(urlp.quote_plus(artist.name), i), headers=HEADERS)
                else:
                    conn.request("GET", "/rest/1.0/artist/{}/setlists?p={}".format(mb_id, i), headers=HEADERS)
                response = conn.getresponse().read()
                conn.close()
            except (TimeoutError, socket.gaierror):
                pass

        main_data = json.loads(response.decode("utf-8"))
        if "code" in main_data and int(main_data["code"]) == 404:
            status.exists = False
            status.save()
            artist.setlistfmstatus_set.clear()
            artist.save()
            artist.delete()
            artist.save()
            break
        setlists = main_data["setlist"]
        total = float(main_data["total"])
        items = float(main_data["itemsPerPage"])
        total /= items
        total = int(total + .5)
        if mb_id is None:
            i += 1
            for setlist in setlists:
                if artist.name.lower() == setlist["artist"]["name"].lower():
                    mb_id = setlist["artist"]["mbid"]
                    artist.mbid = mb_id
                    artist.save()
                    i = 1
                    total = 2
                    break
            continue
        print("Adding {} to Queue".format(i))
        setlist_queue.put((setlists, artist, i, total, status))
        # threading.Thread(target=parse_setlists, args=(setlists, artist, i)).start()
        i+=1
    status.finished = True
    if mb_id is None:
        status.exists = False
    status.published = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status.save()


def parse_setlists(setlists, artist, num=None):
    if num:
        print("In Thread {}".format(num))
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
        fips = get_fips(coordinates)
        venue_name = venue["name"]
        country = city["country"]
        venue_exists = True
        try:
            venue = Venue.objects.get(name__iexact=venue_name)
        except Venue.DoesNotExist:
            venue_exists = False

        if not venue_exists:
            try:
                lat, long = coordinates["lat"], coordinates["long"]
            except KeyError:
                lat, long = -1, -1
            venue = Venue(name=venue_name, city=city["name"], state=state, state_code=state_code,
                          country=country["name"], country_code=country["code"], latitude=lat,
                          longitude=long, fips=fips)
            venue.save()
        sets = []
        encores = []
        for s in setlist["sets"]["set"]:
            songs = []
            for song in s["song"]:
                if "cover" in song:
                    orig_artist = song["cover"]["name"]
                else:
                    orig_artist = artist.name
                try:
                    orig_artist = Artist.objects.get(name__iexact=orig_artist)
                except Artist.DoesNotExist:
                    orig_artist = Artist(name=orig_artist)
                    orig_artist.save()
                try:
                    song = Song.objects.filter(orig_artist=orig_artist).get(song_name=song["name"].strip())
                except Song.DoesNotExist:
                    if song["name"].strip():
                        song = Song(song_name=song["name"].strip())
                        song.save()
                        orig_artist.song_set.add(song)
                        orig_artist.save()
                    else:
                        continue
                if "encore" in s:
                    encores.append(song)
                else:
                    songs.append(song)

            if "encore" not in s and len(songs):
                _set = Set()
                sets.append(_set)
                _set.save()
                for song in songs:
                    _set.songs.add(song)
                    song.set_set.add(_set)
                    _set.save()
                    song.save()

        if len(sets) or len(encores):
            date = datetime.datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d")
            concert = Concert(date=date)
            concert.save()
            artist.concert_set.add(concert)
            if tour is not None:
                try:
                    tour = Tour.objects.get(tour_name=tour)
                except Tour.DoesNotExist:
                    tour = Tour(tour_name=tour)
                    tour.save()
                tour.concert_set.add(concert)
                tour.save()
            for s in sets:
                concert.sets.add(s)
                s.concert_set.add(concert)
                concert.save()
                s.save()
            for song in encores:
                concert.encores.add(song)
                song.concert_set.add(concert)
                song.save()
                concert.save()
            venue.concert_set.add(concert)
            concert.save()
            venue.save()
            artist.save()


def get_fips(coordinates) -> str:
    response = ""
    while not response:
        try:
            census_conn = http.client.HTTPSConnection("geo.fcc.gov")
            census_conn.connect()
            census_conn.request("GET", "/api/census/area?lat={}&lon={}&format=json".format(coordinates["lat"],
                                                                                           coordinates["long"]))
            response = census_conn.getresponse().read()
            census_conn.close()
        except (TimeoutError, socket.gaierror):
            pass

    try:
        response_json = json.loads(response.decode("utf-8"))
        try:
            fips = response_json["results"][0]["county_fips"]
        except (IndexError, AttributeError):  # Non-US Concert
            fips = "NA"
        return fips
    except KeyError:
        return "NA"
