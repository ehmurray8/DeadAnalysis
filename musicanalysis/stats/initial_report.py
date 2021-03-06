from .models import Concert
from .frequency import FrequencyDict
from collections import defaultdict
from .stats_config import TOP_SONGS_BY_DAY, TOP_SONGS_BY_MONTH, TOP_SONGS_BY_YEAR, FILTER_SONGS
from django.db.models import Count, Avg, Q


def artist_concerts(artist):
    concerts = Concert.objects.filter(artist__name__iexact=artist)
    concerts.filter()
    return concerts

def num_encore_songs(concerts):
    return concerts.aggregate(Count('encores'))["encores__count"]

def num_songs(concerts, num_encore_songs):
    total_songs = num_encore_songs + concerts.aggregate(Count('sets__songs'))["sets__songs__count"]
    return total_songs

def covered_artists(concerts):
    return concerts.all().values_list("sets__songs__orig_artist")\
        .annotate(freq=Count("sets__songs__orig_artist")).order_by("freq").reverse()


def basic_info(artist):
    concerts = artist_concerts(artist)
    num_sets = []
    num_covers = 0
    songs = FrequencyDict()
    encores_songs = FrequencyDict()
    originals = FrequencyDict()
    covers = FrequencyDict()
    encores = FrequencyDict()
    covered_artists = FrequencyDict()
    artist_to_songs = defaultdict(list)
    total_cover_plays = 0
    num_covered_plays = 0
    num_no_encores = 0
    for concert in concerts:
        if concert.encores.count():
            encores[" > ".join([song.song_name for song in concert.encores.all()])] += 1
        else:
            num_no_encores += 1
        for es in concert.encores.all():
            if es.orig_artist.name != artist:
                num_covers += 1
                covers[es] += 1
                total_cover_plays += 1
                num_covered_plays += 1
                covered_artists[es.orig_artist] += 1
                artist_to_songs[es.orig_artist] += [es]
            else:
                originals[es] += 1
            songs[es] += 1
            encores_songs[es] += 1
        num_sets.append(concert.sets.count())
        for s in concert.sets.all():
            for song in s.songs.all():
                if song.orig_artist.name != artist:
                    num_covers += 1
                    covers[song] += 1
                    covered_artists[song.orig_artist] += 1
                    total_cover_plays += 1
                    num_covered_plays += 1
                    artist_to_songs[song.orig_artist] += [song]
                else:
                    originals[song] += 1
                songs[song] += 1
    usual_num_sets = max(set(num_sets), key=num_sets.count)
    avg_covers = round(num_covers / concerts.count(), 2)
    songs = ["{} - {}".format(song, num) for song, num in songs.sorted_top_tuples()]
    originals = ["{} - {}".format(song, num) for song, num in  originals.sorted_top_tuples()]
    encores_songs = encores_songs.sorted_top_tuples()
    num_covered_artists = len(set([song.orig_artist for song, _ in covers.sorted_top_tuples()]))
    all_covers = ["{} ({}) - {}".format(song, song.orig_artist, num) for song, num in  covers.sorted_top_tuples()]
    encores = encores.sorted_top_tuples()
    num_solo_encores = sum(1 for _, num in encores if num == 1)
    num_multiple_encores = sum(1 for _, num in encores if num > 1)
    for artist, _songs in artist_to_songs.items():
        song_freqs = []
        for song in set(_songs):
            song_freqs.append((song, covers[song]))
        artist_to_songs[artist] = list(sorted(song_freqs, key=lambda x: x[1], reverse=True))
    return usual_num_sets, avg_covers, songs, originals, encores_songs,\
           all_covers, total_cover_plays, encores, num_solo_encores, num_multiple_encores,\
           num_covered_artists, covered_artists.sorted_top_tuples(), artist_to_songs, num_no_encores


def songs_by_day(concerts, num_concerts):
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    queries = range(1, len(days) + 1)
    return _songs_by(concerts, days, queries, "date__week_day", TOP_SONGS_BY_DAY, num_concerts)


def songs_by_month(concerts, num_concerts):
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
              "November", "December"]
    queries = range(1, len(months) + 1)
    return _songs_by(concerts, months, queries,  "date__month", TOP_SONGS_BY_MONTH, num_concerts)


def songs_by_year(concerts, num_concerts):
    years = list(sorted(set([concert.date.year for concert in concerts.all()])))
    return _songs_by(concerts, years, years, "date__year", TOP_SONGS_BY_YEAR, num_concerts)


def _songs_by(concerts, units, queries, query_str, num_songs, num_concerts):
    songs_list = []
    percents = []
    for i in queries:
        kwargs = {query_str: i}
        _concerts = concerts.filter(**kwargs)
        percents.append(round(( _concerts.count() / num_concerts) * 100, 2))
        frequencies = FrequencyDict()
        for concert in _concerts.all():
            for song in list(concert.encores.all()) + list([song for _set in concert.sets.all() for song in _set.songs.all()]):
                if song.song_name not in FILTER_SONGS:
                    frequencies[song.song_name] += 1
        songs_list.append(frequencies.sorted_top_tuples(num_songs))

    for i, song_list in enumerate(songs_list):
        unique_songs = []
        for song in song_list:
            unique = True
            for j, song_list1 in enumerate(songs_list):
                if i != j:
                    if song[0] in [song1[0] for song1 in song_list1]:
                        unique = False
                        break
            unique_songs.append(unique)
        for k, unique in enumerate(unique_songs):
            songs_list[i][k] = (songs_list[i][k][0], songs_list[i][k][1], unique)

    indexes = [i for i, song_list in enumerate(songs_list) if len(song_list)]
    units = [unit for i, unit in enumerate(units) if i in indexes]
    songs_list = [song_list for i, song_list in enumerate(songs_list) if i in indexes]
    percents = [percent for i, percent in enumerate(percents) if i in indexes]
    return zip(units, songs_list, percents)


def set_info(concerts, num_sets):
    concerts_usual_sets = concerts.annotate(num_sets=Count('sets')).filter(num_sets=num_sets)
    set_lengths = [[] for _ in range(num_sets)]
    sets = [FrequencyDict() for _ in range(num_sets)]
    common_sets = [[] for _ in range(num_sets)]
    common_set_songs = [FrequencyDict() for _ in range(num_sets)]
    num_multiple_sets = [0 for _ in range(num_sets)]
    num_solo_sets = [0 for _ in range(num_sets)]
    dates = [defaultdict(list) for _ in range(num_sets)]

    for concert in concerts_usual_sets:
        for i, s in enumerate(concert.sets.all()):
            set_str = ", ".join([song.song_name for song in s.songs.all()])
            set_lengths[i].append(s.songs.count())
            sets[i].add(set_str)
            dates[i][set_str] += [concert.date]

    for i, s in enumerate(sets):
        common_sets[i] = s.sorted_top_tuples()
        for key, value in common_sets[i]:
            if value > 1:
                num_multiple_sets[i] += 1
            else:
                num_solo_sets[i] += 1
            for song in key.split(", "):
                common_set_songs[i].add(song)

    top_set_dates = [[] for _ in range(num_sets)]
    for i, common_set in enumerate(common_sets):
        for song in common_set:
            top_set_dates[i].append([date.strftime("%B %d, %Y") for date in sorted(dates[i][song[0]])])

    set_lengths = [round(sum(sl)/len(sl), 2) for sl in set_lengths]
    common_set_songs = [common_set_song.sorted_top_tuples() for common_set_song in common_set_songs]
    return set_lengths, num_solo_sets, num_multiple_sets, common_sets, common_set_songs, top_set_dates
