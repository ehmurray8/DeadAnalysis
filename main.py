import os
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader
import datetime
from config import ARTIST, TOP_SONGS_BY_DAY, TOP_SONGS_BY_MONTH, TOP_SONGS_BY_YEAR, NUM_TOP_ENCORES, NUM_TOP_CONCERTS, \
    NUM_TOP_SET_SONGS
from music import FrequencyDict
import get_song_data as gsd


def unique_songs(songs_by):
    elems = [song for song_list in songs_by for song in song_list]
    frequencies = defaultdict(int)
    for elem in elems:
        frequencies[elem[0]] += 1
    unique = [song for song, num in frequencies.items() if num == 1]
    return unique


if __name__ == "__main__":
    # gsd.get_song_data()
    music = gsd.get_pickled_song_data()
    file_loader = FileSystemLoader("templates")
    env = Environment(loader=file_loader)
    template = env.get_template("output_template.jinja2")
    kwargs = {}
    set_lengths, encore_length, common_sets, common_encores, num_solo_sets,  num_multiple_sets,\
        num_solo_encore, num_multiple_encores, common_set_songs, top_set_dates, \
        avg_concert_length, avg_covers = music.basic_concert_info()

    encore_songs = FrequencyDict()
    for set, num in common_encores:
        for song in set:
            encore_songs.add(song, num)

    kwargs["avg_covers"] = avg_covers
    kwargs["concert_len"] = avg_concert_length
    kwargs["num_concerts"] = len(music.concerts)
    kwargs["num_solo_sets"] = num_solo_sets
    kwargs["num_multiple_sets"] = num_multiple_sets
    kwargs["num_solo_encores"] = num_solo_encore
    kwargs["num_multiple_encores"] = num_multiple_encores
    kwargs["common_sets"] = [css[:NUM_TOP_CONCERTS] for css in common_sets]
    kwargs["top_set_dates"] = top_set_dates
    kwargs["num_sets"] = len(set_lengths)
    kwargs["set_lengths"] = enumerate(set_lengths)
    kwargs["encore_length"] = encore_length
    kwargs["common_set_songs"] = [css[:NUM_TOP_SET_SONGS] for css in common_set_songs]
    kwargs["uncommon_set_songs"] = [list(reversed(css))[:NUM_TOP_SET_SONGS] for css in common_set_songs]
    kwargs["common_encores"] = common_encores[:NUM_TOP_ENCORES]
    kwargs["common_encore_songs"] = encore_songs.sorted_top_tuples(num=NUM_TOP_ENCORES)
    kwargs["uncommon_encore_songs"] = list(reversed(common_encores))[:NUM_TOP_ENCORES]
    songs_by_day, percents, songs_total = music.songs_by_day(TOP_SONGS_BY_DAY)
    uniques = unique_songs(songs_by_day)
    songs_by_day = [(song[0], song[1], True if song[0] in uniques else False)
                    for song_list in songs_by_day for song in song_list]
    songs_by_day = [songs_by_day[i:i+TOP_SONGS_BY_DAY] for i in range(0, len(songs_by_day), TOP_SONGS_BY_DAY)]
    percents = ["{}, {}%".format(total, round(perc * 100, 2)) for perc, total in zip(percents, songs_total)]
    kwargs["day_song_zip_info"] = zip(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
                                   "Sunday"], songs_by_day, percents)
    songs_by_month, percents, songs_total = music.songs_by_month(TOP_SONGS_BY_MONTH)
    uniques = unique_songs(songs_by_month)
    songs_by_month = [(song[0], song[1], True if song[0] in uniques else False)
                      for song_list in songs_by_month for song in song_list]
    songs_by_month = [songs_by_month[i:i+TOP_SONGS_BY_MONTH] for i in range(0, len(songs_by_month), TOP_SONGS_BY_MONTH)]
    percents = ["{}, {}%".format(total, round(perc * 100, 2)) for perc, total in zip(percents, songs_total)]
    kwargs["month_song_zip_info"] = zip(["January", "February", "March", "April", "May", "June", "July", "August",
                                         "September", "October", "November", "December"], songs_by_month, percents)
    songs_by_year, percents, songs_total = music.songs_by_year(TOP_SONGS_BY_YEAR)
    uniques = unique_songs(songs_by_year)
    songs_by_year = [(song[0], song[1], True if song[0] in uniques else False)
                     for song_list in songs_by_year for song in song_list]
    songs_by_year = [songs_by_year[i:i+TOP_SONGS_BY_YEAR]
                     for i in range(0, len(songs_by_year), TOP_SONGS_BY_YEAR)]
    percents = ["{}, {}%".format(total, round(perc * 100, 2)) for perc, total in zip(percents, songs_total)]
    year_song_zip_info = []
    for year, song_list, percent in zip(range(music.start_year(), datetime.datetime.now().year+1, 1),
                                        songs_by_year, percents):
        if percent != "0.0%":
            year_song_zip_info.append((year, song_list, percent))
    kwargs["year_song_zip_info"] = year_song_zip_info
    top_songs = music.top_songs(50)
    kwargs["top_songs"] = len(top_songs)
    kwargs["top_songs_list"] = ["{} - {}".format(song, num) for song, num in top_songs]
    kwargs["county_graph"], kwargs["state_graph"], kwargs["world_graph"] = music.get_maps()
    kwargs["all_songs"] , kwargs["all_covers"], kwargs["all_originals"], kwargs["total_songs"] = music.all_song_info()
    kwargs["artist"] = ARTIST
    kwargs["style_url"] = os.path.join(os.getcwd(), "static", "stylesheet.css")

    top_cover_artists, total_cover_plays, artist_to_song, total_artists_covered = music.cover_info()
    kwargs["total_cover_plays"] = total_cover_plays
    kwargs["all_covered_artists"] = top_cover_artists
    kwargs["artist_to_songs"] = artist_to_song
    kwargs["total_artists_covered"] = total_artists_covered
    output = template.render(**kwargs)
    if not os.path.isdir(r"html\{}".format(ARTIST)):
        os.mkdir(r"html\{}".format(ARTIST))
    with open(r"html\{}\output.html".format(ARTIST), "w", encoding="utf-8") as f:
        f.write(output)
