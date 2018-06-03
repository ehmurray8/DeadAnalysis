from .models import Concert
from .frequency import FrequencyDict
from collections import defaultdict


# TODO: Add helper methods to create initial view
def basic_info(artist):
    concerts = Concert.objects.filter(artist__name=artist)
    num_concerts = len(concerts)
    total_songs = 0
    num_sets = []
    num_covers = 0
    songs = FrequencyDict()
    encores_songs = FrequencyDict()
    originals = FrequencyDict()
    covers = FrequencyDict()
    encores = FrequencyDict()
    covered_artists = FrequencyDict()
    encore_length = []
    total_cover_plays = 0
    num_covered_plays = 0
    for concert in concerts:
        total_songs += concert.encores.count()
        encore_length.append(concert.encores.count())
        encores[" > ".join([song.song_name for song in concert.encores.all()])] += 1
        for es in concert.encores.all():
            if es.orig_artist.name != artist:
                num_covers += 1
                covers[es] += 1
                total_cover_plays += 1
                num_covered_plays += 1
                covered_artists[es.orig_artist] += 1
            else:
                originals[es] += 1
            songs[es] += 1
            encores_songs[es] += 1
        num_sets.append(concert.sets.count())
        for s in concert.sets.all():
            total_songs += s.songs.count()
            for song in s.songs.all():
                if song.orig_artist.name != artist:
                    num_covers += 1
                    covers[song] += 1
                    covered_artists[song.orig_artist] += 1
                    total_cover_plays += 1
                    num_covered_plays += 1
                else:
                    originals[song] += 1
                songs[song] += 1
    usual_num_sets = max(set(num_sets), key=num_sets.count)
    concert_len = round(total_songs / num_concerts, 2)
    avg_covers = round(num_covers / num_concerts, 2)
    songs = ["{} - {}".format(song, num) for song, num in songs.sorted_top_tuples()]
    originals = ["{} - {}".format(song, num) for song, num in  originals.sorted_top_tuples()]
    encores_songs = encores_songs.sorted_top_tuples()
    covers = ["{} - {}".format(song, num) for song, num in  covers.sorted_top_tuples()]
    avg_encore_length = round(sum(encore_length) / len(encore_length), 2)
    encores = encores.sorted_top_tuples()
    num_solo_encores = sum(1 for _, num in encores if num == 1)
    num_multiple_encores = sum(1 for _, num in encores if num > 1)
    return num_concerts, total_songs, usual_num_sets, concert_len, avg_covers, songs, originals, encores_songs, covers,\
           total_cover_plays, avg_encore_length, encores, num_solo_encores, num_multiple_encores, num_covered_plays,\
           covered_artists.sorted_top_tuples()


def set_info(artist, num_sets):
    concerts = Concert.objects.filter(artist__name=artist)
    concerts_usual_sets = [concert for concert in concerts if len(concert.sets) == num_sets]
    set_lengths = [[] for _ in range(num_sets)]
    sets = [FrequencyDict() for _ in range(num_sets)]
    dates = [defaultdict(list) for _ in range(num_sets)]
    for concert in concerts_usual_sets:
        for i, s in enumerate(concert.sets):
            set_lengths[i].append(len(s))
            sets[i].add(s)
            dates[i][s] += [concert.date]
