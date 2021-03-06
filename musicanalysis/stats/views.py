from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from stats.tasks import get_song_data, setup_status
import urllib.parse as urlp
import json
from .models import SetlistFMStatus, Artist, Venue
from .map_helper import create_graph_code
from .initial_report import basic_info, songs_by_day, songs_by_month, songs_by_year, set_info, artist_concerts, \
    num_songs, num_encore_songs, covered_artists
from .stats_config import TOP_SONGS, NUM_TOP_SET_SONGS, NUM_TOP_SETS, NUM_TOP_ENCORES, NUM_TOP_COVERS, NUM_TOP_VENUES
from .frequency import FrequencyDict
from musicanalysis._keys import GOOGLE_MAPS_KEY, MB_UNAME, MB_PASSWORD
import musicbrainzngs as mb


def _get_statuses():
    statuses = {}
    try:
        for _status in SetlistFMStatus.objects.filter(finished=False).all():
            try:
                percent = int(float(_status.current_page/_status.final_page) * 100)
            except (ValueError, ZeroDivisionError):
                percent = 0
            if not percent:
                percent = 1
            statuses[_status.artist.name] = percent
    except SetlistFMStatus.DoesNotExist:
        pass
    return statuses


# Create your views here.
def index(request):
    search_musician = request.GET.get('search-musician', '')
    context = {}
    msgs = messages.get_messages(request)
    if msgs:
        context["search_status"] = ", ".join([str(msg) for msg in msgs])

    context["artists"] = [artist.name for artist in Artist.objects.all() if len(artist.concert_set.all())
                          and SetlistFMStatus.objects.filter(artist__name__iexact=artist.name, finished=True).exists()]
    context["in_progress_artists"] = _get_statuses()
    if search_musician:
        search_musician = urlp.unquote(search_musician, encoding="utf-8")
        try:
            setlist_query = SetlistFMStatus.objects.get(exists=False, artist__name__iexact=search_musician)
            setlist_query.alerted = True
            setlist_query.save()
            ss = "No data for {} on setlist.fm.".format(search_musician)
            messages.add_message(request, messages.INFO, ss)
            return redirect("stats:index")
        except SetlistFMStatus.DoesNotExist:
            pass

        if Artist.objects.filter(name=search_musician).exists and \
                SetlistFMStatus.objects.filter(artist__name__iexact=search_musician, finished=True).exists():
            return redirect('stats:artist', artist=search_musician)
        elif SetlistFMStatus.objects.filter(finished=False, exists=True, artist__name__iexact=search_musician).exists():
            ss = "Downloading setlist.fm data in progress, for {}.".format(search_musician)
            messages.add_message(request, messages.INFO, ss)
            return redirect("stats:index")
        else:
            _, __ = setup_status(search_musician)
            context["in_progress_artists"] = _get_statuses()
            get_song_data.delay(search_musician)
            ss = "Unable to find {}, attempting to download artist information from setlist.fm.".format(search_musician)
            messages.add_message(request, messages.INFO, ss)
            return redirect('stats:index')

    artists = []
    try:
        setlist_queries = SetlistFMStatus.objects.filter(exists=False, alerted=False)
        for setlist_query in setlist_queries:
            setlist_query.alerted = True
            setlist_query.save()
            artists.append(setlist_query.artist.name)
    except SetlistFMStatus.DoesNotExist:
        pass

    if len(artists):
        ss = "No data for {} on setlist.fm.".format(", ".join(artists))
        context["search_status"] = ss
        return render(request, 'stats/index.jinja2', context=context)

    return render(request, 'stats/index.jinja2', context=context)


def status(request):
    context = {}
    context["in_progress_artists"] = list(sorted([percent for _, percent in _get_statuses().items()], reverse=True))
    return HttpResponse(json.dumps(context))


def lat_longs(artist):
    artist_name = urlp.unquote(artist, encoding="utf-8")
    venues = Venue.objects.filter(concert__artist__name__iexact=artist_name).all()
    venue_frequencies = FrequencyDict()
    for venue in venues:
        venue_frequencies[venue] += 1
    return venue_frequencies


def venue_locations(request, artist):
    locs = []
    venue_frequencies = lat_longs(artist)
    for i, (venue, num) in enumerate(venue_frequencies):
        locs.append(["{} - {}".format(venue.name, num), venue.latitude, venue.longitude, i])
    return HttpResponse(json.dumps({"locations": locs}))


def artist(request, artist):
    context = {}
    context["artist"] = artist
    return render(request, 'stats/artist.jinja2', context)


def initial(request, artist):
    context = {}
    context["artist"] = artist
    context["api_key"] = GOOGLE_MAPS_KEY

    usual_num_sets, avg_covers, all_songs, all_originals, encore_songs,\
        all_covers, total_cover_plays, encores, num_solo_encores, num_multiple_encores,\
        num_covered_artists, _covered_artists, artist_to_songs, num_no_encores = basic_info(artist)

    concerts = artist_concerts(artist)
    num_concerts = concerts.count()
    total_encore_songs = num_encore_songs(concerts)
    total_songs = num_songs(concerts, total_encore_songs)
    covered = covered_artists(concerts)

    context["num_concerts"] = num_concerts
    context["total_songs"] = total_songs
    context["num_sets"] = usual_num_sets
    context["avg_covers"] = avg_covers
    context["concert_len"] = round(total_songs/num_concerts, 2)

    set_lengths, num_solo_sets, num_multiple_sets, common_sets, common_set_songs, top_set_days = \
        set_info(artist, usual_num_sets)

    context["set_lengths"] = set_lengths
    context["num_solo_sets"] = num_solo_sets
    context["num_multiple_sets"] = num_multiple_sets
    context["common_set_songs"] = [css[:NUM_TOP_SET_SONGS] for css in common_set_songs]
    context["uncommon_set_songs"] = [list(reversed(css))[:NUM_TOP_SET_SONGS] for css in common_set_songs]
    context["common_sets"] = [cs[:NUM_TOP_SETS] for cs in common_sets]
    context["top_set_dates"] = top_set_days

    context["encore_length"] = round(total_encore_songs/num_concerts, 2)
    context["num_solo_encores"] = num_solo_encores
    context["num_multiple_encores"] = num_multiple_encores
    context["common_encores"] = encores[:NUM_TOP_ENCORES]
    context["common_encore_songs"] = encore_songs[:NUM_TOP_ENCORES]
    context["num_no_encores"] = num_no_encores
    context["top_songs"] = TOP_SONGS

    context["day_song_zip_info"] = songs_by_day(concerts, num_concerts)
    context["month_song_zip_info"] = songs_by_month(concerts, num_concerts)
    context["year_song_zip_info"] = songs_by_year(concerts, num_concerts)

    context["county_graph"], context["state_graph"], context["country_graph"] = create_graph_code(artist)

    context["all_songs"] = all_songs
    context["all_originals"] = all_originals
    context["total_cover_plays"] = total_cover_plays
    context["all_covers"] = all_covers
    context["total_artists_covered"] = num_covered_artists
    context["all_covered_artists"] = _covered_artists[:NUM_TOP_COVERS]
    context["artist_to_songs"] = artist_to_songs

    venue_frequencies = lat_longs(artist)
    loc_frequencies = [(str(venue), num) for venue, num in venue_frequencies.sorted_top_tuples()]
    context["loc_frequencies"] = loc_frequencies[:NUM_TOP_VENUES]

    return render(request, 'stats/initial_artist.jinja2', context=context)

def typical_concert(request, artist):
    context = {}
    context["artist"] = artist

    usual_num_sets, avg_covers, all_songs, all_originals, encore_songs, \
    all_covers, total_cover_plays, encores, num_solo_encores, num_multiple_encores, \
    num_covered_artists, covered_artists, artist_to_songs, num_no_encores = basic_info(artist)

    concerts = artist_concerts(artist)
    num_concerts = concerts.count()
    total_encore_songs = num_encore_songs(concerts)
    total_songs = num_songs(concerts, total_encore_songs)

    context["num_concerts"] = num_concerts
    context["total_songs"] = total_songs
    context["num_sets"] = usual_num_sets
    context["avg_covers"] = avg_covers
    context["concert_len"] = round(total_songs/num_concerts, 2)

    set_lengths, num_solo_sets, num_multiple_sets, common_sets, common_set_songs, top_set_days = \
        set_info(concerts, usual_num_sets)

    context["set_lengths"] = set_lengths
    context["num_solo_sets"] = num_solo_sets
    context["num_multiple_sets"] = num_multiple_sets
    context["common_set_songs"] = [css[:NUM_TOP_SET_SONGS] for css in common_set_songs]
    context["uncommon_set_songs"] = [list(reversed(css))[:NUM_TOP_SET_SONGS] for css in common_set_songs]
    context["common_sets"] = [cs[:NUM_TOP_SETS] for cs in common_sets]
    context["top_set_dates"] = top_set_days

    context["encore_length"] = round(total_encore_songs/num_concerts, 2)
    context["num_solo_encores"] = num_solo_encores
    context["num_multiple_encores"] = num_multiple_encores
    context["common_encores"] = encores[:NUM_TOP_ENCORES]
    context["common_encore_songs"] = encore_songs[:NUM_TOP_ENCORES]
    context["num_no_encores"] = num_no_encores
    context["top_songs"] = TOP_SONGS
    context["all_songs"] = all_songs

    return render(request, 'stats/typical_concert.jinja2', context=context)

def locations(request, artist):
    context = {}
    context["artist"] = artist
    context["county_graph"], context["state_graph"], context["country_graph"] = create_graph_code(artist)
    return render(request, 'stats/locations.jinja2', context=context)

def songs(request, artist):
    context = {}
    context["artist"] = artist
    # TODO: Break this into one method
    usual_num_sets, avg_covers, all_songs, all_originals, encore_songs, all_covers, total_cover_plays, encores,\
        num_solo_encores, num_multiple_encores,  num_covered_artists, covered_artists, artist_to_songs, num_no_encores\
        = basic_info(artist)

    context["all_songs"] = all_songs
    context["all_originals"] = all_originals
    return render(request, 'stats/songs.jinja2', context=context)

def covers(request, artist):
    context = {}
    context["artist"] = artist
    # TODO: Break this into one method
    usual_num_sets, avg_covers, all_songs, all_originals, encore_songs, all_covers, total_cover_plays, encores, \
    num_solo_encores, num_multiple_encores,  num_covered_artists, _covered_artists, artist_to_songs, num_no_encores \
        = basic_info(artist)

    concerts = artist_concerts(artist)
    covered = covered_artists(concerts)

    context["total_cover_plays"] = total_cover_plays
    context["all_covers"] = all_covers
    context["total_artists_covered"] = num_covered_artists
    context["all_covered_artists"] = _covered_artists[:NUM_TOP_COVERS]
    context["artist_to_songs"] = artist_to_songs
    return render(request, 'stats/covers.jinja2', context=context)

def tours(request, artist):
    context = {}
    context["artist"] = artist
    return render(request, 'stats/tours.jinja2', context=context)

def venues(request, artist):
    context = {}
    context["artist"] = artist
    context["api_key"] = GOOGLE_MAPS_KEY
    venue_frequencies = lat_longs(artist)
    loc_frequencies = [(str(venue), num) for venue, num in venue_frequencies.sorted_top_tuples()]
    context["loc_frequencies"] = loc_frequencies[:NUM_TOP_VENUES]
    return render(request, 'stats/venues.jinja2', context=context)

def songs_by(request, artist):
    context = {}
    context["artist"] = artist
    concerts = artist_concerts(artist)
    num_concerts = concerts.count()
    context["day_song_zip_info"] = songs_by_day(concerts, num_concerts)
    context["month_song_zip_info"] = songs_by_month(concerts, num_concerts)
    context["year_song_zip_info"] = songs_by_year(concerts, num_concerts)
    return render(request, 'stats/songs_by.jinja2', context=context)

def download_artist(request):
    search_musician = request.GET.get('search-musician', '')
    mb.auth(MB_UNAME, MB_PASSWORD)
    if search_musician:
        artists = mb.search_artists(search_musician)
        disp_artists = []
        for artist in artists["artist-list"]:
            name = artist["name"]
            _type = artist["type"]
