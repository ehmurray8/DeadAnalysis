import json
import http.client
import datetime
import urllib.parse as urlp
from django.conf import settings
from .models import Song, Set, Concert, Venue, Tour, Artist, SetlistFMStatus
from musicanalysis.celery import app
import logging

logger = logging.getLogger(__name__)


HEADERS = {
    'x-api-key': settings.SETLIST_FM_API_KEY,
    'accept': "application/json",
    'cache-control': "no-cache",
}


def setup_status(artist):
    urlp.unquote(artist, encoding="utf-8")
    artist = Artist.objects.get_or_create(name=artist)
    try:
        status = SetlistFMStatus.objects.filter(artist=artist)[0]
        status.finished = False
        status.published = None
        status.started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status.save()
    except (IndexError, SetlistFMStatus.DoesNotExist):
        status = SetlistFMStatus()
        status.save()
        artist.setlistfmstatus_set.add(status)
        artist.save()
    return artist, status


@app.task
def get_song_data(artist):
    total = 2
    i = 1
    artist, status = setup_status(artist)
    while i <= total:
        conn = http.client.HTTPSConnection("api.setlist.fm")
        conn.connect()
        logger.info("{} Page {}".format(artist.name, i))
        conn.request("GET", "/rest/1.0/search/setlists?artistName={}&p={}" .format(urlp.quote_plus(artist.name), i),
                     headers=HEADERS)
        res = conn.getresponse()
        data = res.read()
        main_data = json.loads(data.decode("utf-8"))
        if "code" in main_data and int(main_data["code"]) == 404:
            status.exists = False
            status.save()
            artist.delete()
            artist.save()
            break
        setlists = main_data["setlist"]
        total = float(main_data["total"])
        items = float(main_data["itemsPerPage"])
        total /= items
        total = int(total + .5)
        status.current_page = i
        status.final_page = total
        status.save()
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
            try:
                lat, long = coordinates["lat"], coordinates["long"]
            except KeyError:
                lat, long = -1, -1
            venue = Venue.objects.get_or_create(name=venue["name"], city=city["name"], state=state, state_code=state_code,
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
                        orig_artist = Artist.objects.get(name=orig_artist)
                    except Artist.DoesNotExist:
                        orig_artist = Artist(name=orig_artist)
                        orig_artist.save()
                    try:
                        song = Song.objects.filter(orig_artist=orig_artist).get(song_name=song["name"])
                    except Song.DoesNotExist:
                        song = Song(song_name=song["name"])
                        song.save()
                        orig_artist.song_set.add(song)
                        orig_artist.save()
                    if "encore" in s:
                        encores.append(song)
                    else:
                        songs.append(song)

                if "encore" not in s:
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
        i+=1
        conn.close()
    status.finished=True
    status.published = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_fips(coords) -> str:
    census_conn = http.client.HTTPSConnection("geo.fcc.gov")
    census_conn.connect()
    try:
        census_conn.request("GET", "/api/census/area?lat={}&lon={}&format=json".format(coords["lat"], coords["long"]))
        response = census_conn.getresponse().read()
        response_json = json.loads(response.decode("utf-8"))
        try:
            fips = response_json["results"][0]["county_fips"]
        except (IndexError, AttributeError):  # Non-US Concert
            fips = "NA"
        census_conn.close()
        return fips
    except KeyError:
        census_conn.close()
        return "NA"