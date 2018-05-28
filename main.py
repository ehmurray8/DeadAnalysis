import os
from jinja2 import Environment, FileSystemLoader
import datetime
from config import ARTIST
import get_song_data as gsd
import map_test

if __name__ == "__main__":
    # gsd.get_song_data()
    music = gsd.get_pickled_song_data()
    file_loader = FileSystemLoader("templates")
    env = Environment(loader=file_loader)
    template = env.get_template("output_template.html")
    kwargs = {}
    songs_by_day, percents = music.songs_by_day(10)
    percents = ["{}%".format(round(perc * 100, 2)) for perc in percents]
    kwargs["day_song_zip_info"] = zip(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
                                   "Sunday"], songs_by_day, percents)
    songs_by_month, percents = music.songs_by_month(10)
    percents = ["{}%".format(round(perc * 100, 2)) for perc in percents]
    kwargs["month_song_zip_info"] = zip(["January", "February", "March", "April", "May", "June", "July", "August",
                                         "September", "October", "November", "December"], songs_by_month, percents)
    songs_by_year, percents = music.songs_by_year(10)
    percents = ["{}%".format(round(perc * 100, 2)) for perc in percents]
    year_song_zip_info = []
    for year, song_list, percent in zip(range(music.start_year(), datetime.datetime.now().year+1, 1),
                                        songs_by_year, percents):
        if percent != "0.0%":
            year_song_zip_info.append((year, song_list, percent))
    kwargs["year_song_zip_info"] = year_song_zip_info
    top_songs = music.top_songs(50)
    kwargs["top_songs"] = len(top_songs)
    kwargs["top_songs_list"] = ["{} - {}".format(song, num) for song, num in top_songs]
    kwargs["county_graph"], kwargs["state_graph"], kwargs["world_graph"] = map_test.create_graph_code()
    kwargs["all_songs"] , kwargs["all_covers"], kwargs["all_originals"] = music.all_song_info()
    kwargs["num_songs"] = len(kwargs["all_songs"])
    kwargs["num_covers"] = len(kwargs["all_covers"])
    kwargs["num_originals"] = len(kwargs["all_originals"])
    kwargs["artist"] = ARTIST
    output = template.render(**kwargs)
    if not os.path.isdir(r"html\{}".format(ARTIST)):
        os.mkdir(r"html\{}".format(ARTIST))
    with open(r"html\{}\output.html".format(ARTIST), "w", encoding="utf-8") as f:
        f.write(output)
