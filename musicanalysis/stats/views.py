from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from stats.tasks import get_song_data, setup_status
import urllib.parse as urlp
from .models import SetlistFMStatus, Artist
import json


# Create your views here.
def index(request):
    search_musician = request.GET.get('search-musician', '')
    status = request.GET.get('status', '')
    search_status = request.GET.get('search-status', '')
    context = {}
    statuses = {}
    for _status in SetlistFMStatus.objects.filter(finished=False):
        if _status.current_page != _status.final_page:
            try:
                percent = int(float(_status.current_page/_status.final_page) * 100)
            except (ValueError, ZeroDivisionError):
                percent = 0
            if not percent:
                percent = 1
            statuses[_status.artist.name] = percent
    context["in_progress_artists"] = statuses

    if search_musician:
        search_musician = urlp.unquote(search_musician, encoding="utf-8")
        try:
            setlist_query = SetlistFMStatus.objects.get(exists=False, artist__name=search_musician)
            setlist_query.alerted = True
            setlist_query.save()
            ss = "No data for {} on setlist.fm.".format(search_musician)
            context["search_status"] = ss
            return render(request, 'stats/index.jinja2', context)
        except SetlistFMStatus.DoesNotExist:
            pass

        if Artist.objects.filter(name=search_musician).exists and \
                SetlistFMStatus.objects.filter(artist__name=search_musician, finished=True).exists():
            return redirect('stats:artist', artist=search_musician)
        elif SetlistFMStatus.objects.filter(finished=False, exists=True, arti__name=search_musician).exists():
            ss = "Downloaing setlist.fm data in progress, for {}.".format(search_musician)
            return render(request, 'stats/index.jinja2', context=ss)
        else:
            setup_status(search_musician)
            get_song_data.delay(search_musician)
            ss = "Unable to find {}, attempting to download artist information from setlist.fm.".format(search_musician)
            context["search_status"] = ss
            return render(request, 'stats/index.jinja2', context=context)

    setlist_queries = SetlistFMStatus.objects.filter(exists=False, alerted=False)
    artists = []
    for setlist_query in setlist_queries:
        setlist_query.alerted = True
        setlist_query.save()
        artists.append(setlist_query.artist.name)

    if len(artists):
        ss = "No data for {} on setlist.fm.".format(", ".join(artists))
        context["search_status"] = ss
        return render(request, 'stats/index.jinja2', context=context)

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
