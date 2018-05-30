import os
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader
import datetime
from config import ARTIST, TOP_SONGS_BY_DAY, TOP_SONGS_BY_MONTH, TOP_SONGS_BY_YEAR
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
        num_solo_encore, num_multiple_encores, common_set_songs, top_set_dates, uncommon_set_songs,\
        avg_concert_length= music.basic_concert_info()

    kwargs["concert_len"] = avg_concert_length
    kwargs["num_concerts"] = len(music.concerts)
    kwargs["num_solo_sets"] = num_solo_sets
    kwargs["num_multiple_sets"] = num_multiple_sets
    kwargs["num_solo_encores"] = num_solo_encore
    kwargs["num_multiple_encores"] = num_multiple_encores
    kwargs["common_sets"] = common_sets
    kwargs["top_set_dates"] = top_set_dates
    kwargs["num_sets"] = len(set_lengths)
    kwargs["set_lengths"] = enumerate(set_lengths)
    kwargs["encore_length"] = encore_length
    kwargs["common_set_songs"] = common_set_songs
    kwargs["common_encore_songs"] = common_encores
    kwargs["uncommon_set_songs"] = uncommon_set_songs
    kwargs["uncommon_encores"] = list(reversed(common_encores))
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
    kwargs["all_songs"] , kwargs["all_covers"], kwargs["all_originals"] = music.all_song_info()
    kwargs["num_songs"] = len(kwargs["all_songs"])
    kwargs["num_covers"] = len(kwargs["all_covers"])
    kwargs["num_originals"] = len(kwargs["all_originals"])
    kwargs["artist"] = ARTIST
    kwargs["style_url"] = os.path.join(os.getcwd(), "static", "stylesheet.css")
    output = template.render(**kwargs)
    if not os.path.isdir(r"html\{}".format(ARTIST)):
        os.mkdir(r"html\{}".format(ARTIST))
    with open(r"html\{}\output.html".format(ARTIST), "w", encoding="utf-8") as f:
        f.write(output)
