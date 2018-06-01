from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from stats.tasks import get_song_data, setup_status
import urllib.parse as urlp
from .models import SetlistFMStatus, Artist
import json


def _get_statuses():
    statuses = {}
    try:
        for _status in SetlistFMStatus.objects.filter(finished=False):
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
                          and SetlistFMStatus.objects.filter(artist__name=artist.name, finished=True).exists()]
    context["in_progress_artists"] = _get_statuses()
    if search_musician:
        search_musician = urlp.unquote(search_musician, encoding="utf-8")
        try:
            setlist_query = SetlistFMStatus.objects.get(exists=False, artist__name=search_musician)
            setlist_query.alerted = True
            setlist_query.save()
            ss = "No data for {} on setlist.fm.".format(search_musician)
            messages.add_message(request, messages.INFO, ss)
            return redirect("stats:index")
        except SetlistFMStatus.DoesNotExist:
            pass

        if Artist.objects.filter(name=search_musician).exists and \
                SetlistFMStatus.objects.filter(artist__name=search_musician, finished=True).exists():
            return redirect('stats:artist', artist=search_musician)
        elif SetlistFMStatus.objects.filter(finished=False, exists=True, artist__name=search_musician).exists():
            ss = "Downloaing setlist.fm data in progress, for {}.".format(search_musician)
            messages.add_message(request, messages.INFO, ss)
            return redirect("stats:index")
        else:
            setup_status(search_musician)
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


def artist(request, artist):
    context = {}
    context["artist"] = artist
    return render(request, 'stats/artist.jinja2', context)


def initial(request):
    pass
