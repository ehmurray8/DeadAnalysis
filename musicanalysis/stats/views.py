from django.shortcuts import render, redirect
from django.http import HttpResponse
from stats.tasks import get_song_data, setup_status
import urllib.parse as urlp
from .models import SetlistFMStatus, Artist
import json


# Create your views here.
def index(request, search_status=""):
    search_musician = request.GET.get('search-musician', '')
    status = request.GET.get('status', '')
    search_musician = urlp.unquote(search_musician, encoding="utf-8")
    if search_musician:
        setlist_queries = SetlistFMStatus.objects.filter(exists=False, artist=search_musician)
        if len(setlist_queries):
            for sq in setlist_queries:
                sq.alerted = True
                sq.save()
            ss = "No data for {} on setlist.fm.".format(search_musician)
            return redirect('stats:index', search_status=ss)
        elif Artist.objects.filter(name=search_musician).exists():
            if SetlistFMStatus.objects.get(artist__name=search_musician).exists():
                return redirect('stats:artist', artist=search_musician)
        else:
            setup_status(search_musician)
            get_song_data.delay(search_musician)
            ss = "Unable to find artist, attempting to download artist information from setlist.fm."
            return redirect('stats:index', search_status=ss)

    context = {}
    statuses = {}

    setlist_queries = SetlistFMStatus.objects.filter(exists=False, alerted=False)
    artists = []
    for setlist_query in setlist_queries:
        setlist_query.alerted = True
        setlist_query.save()
        artists.append(setlist_query.artist.name)

    if len(artists):
        ss = "No data for {} on setlist.fm.".format(", ".join(artists))
        return redirect('stats:index', search_status=ss)

    for _status in SetlistFMStatus.objects.filter(finished=False):
        if _status.current_page != _status.final_page:
            try:
                statuses[_status.artist.name] = int(float(_status.current_page/_status.final_page) * 100)
            except (ValueError, ZeroDivisionError):
                statuses[_status.artist.name] = 0

    context["in_progress_artists"] = statuses
    if status:
        context["in_progress_artists"] = [percent for _, percent in context["in_progress_artists"].items()]
        return HttpResponse(json.dumps(context))

    context["artists"] = [artist.name for artist in Artist.objects.all() if len(artist.concert_set.all())
                          and SetlistFMStatus.objects.filter(artist__name=artist.name, finished=True).exists()]
    context["search_status"] = search_status

    return render(request, 'stats/index.jinja2', context)


def artist(request, artist):
    context = {}
    context["artist"] = artist
    return render(request, 'stats/artist.jinja2', context)
