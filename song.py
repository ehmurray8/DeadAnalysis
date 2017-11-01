import calendar
import datetime
import numpy as np
from collections import OrderedDict
from config import ARTISTS, SELECTED_COVERS

class Location(object):
    def __init__(self, city, state, country, venue, coords):
        self.city = city
        self.state = state
        self.country = country
        self.venue = venue
        self.latitude = coords["lat"]
        self.longitude = coords["long"]
    

class Song(object):
    def __init__(self, loc, date, tour, artist, orig_artist, name):
        self.location = loc
        self.date = datetime.datetime.strptime(date, "%d-%m-%Y").date()
        self.artist = artist
        self.orig_artist = orig_artist
        self.name = name

    def get_weekday(self):
        #calendar.day_name[self.date.weekday()]
        return self.date.weekday()

    def is_cover(self):
        if self.artist != self.orig_artist:
            return True
        return False

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class Band(object):
    def __init__(self):
        self.all_songs = SongCont()
        self.all_covers = SongCont()
        self.all_originals = SongCont()

    def num_covers(self):
        return len(self.all_covers)

    def num_songs(self):
        return len(self.all_songs)

    def num_originals(self):
        return len(self.all_originals)

    def selected_cover_songs(self):
        chosen_covers = [SongCont() for _ in range(len(SELECTED_COVERS))]
        for artist, cc in zip(SELECTED_COVERS, chosen_covers):
            for cover in self.all_covers.all:
                if cover.orig_artist == artist:
                    cc.add(cover)
        return chosen_covers

    def __str__(self):
        all = "\n\nAll songs frequencies:\n{}\nNumber of total songs: {}\n" \
                    .format(self.all_songs.sorted_list(), self.num_songs())
        covers = "All covers frequencies:\n{}\nNumber of cover songs: {}\n" \
                    .format(self.all_covers.sorted_list(), self.num_covers())
        orig = "All original songs frequencies:\n{}\nNumber of original songs: {}\n\n" \
                    .format(self.all_originals.sorted_list(), self.num_originals())
        covs = "\n"
        for artist, songs in zip(SELECTED_COVERS, self.selected_cover_songs()):
            covs += "\n".join([artist, str(songs.sorted_list())])
            covs += "\nNumber of covered songs: {}\n".format(len(songs.sorted_list()))
        return "\n".join([all, covers, orig, covs])
        
    def __repr__(self):
        all = "\n\nAll songs frequencies:\n{}\nNumber of total songs: {}\n" \
                    .format(self.all_songs.sorted_list(), self.num_songs())
        covers = "All covers frequencies:\n{}\nNumber of cover songs: {}\n" \
                    .format(self.all_covers.sorted_list(), self.num_covers())
        orig = "All original songs frequencies:\n{}\nNumber of original songs: {}\n\n" \
                    .format(self.all_originals.sorted_list(), self.num_originals())
        covs_str = "".join(SELECTED_COVERS)
        selected_covs = self.selected_cover_songs().sorted_list()
        covs= "\nSelected Covered Artists:\n{}\nNumber of covered songs: {}\n" \
                    .format(self.selected_covs, len(selected_covs))
        return "\n".join([all, covers, orig, covs])


class MusicData(object):
    def __init__(self):
        self.bands = OrderedDict()
        for artist in ARTISTS:
            self.bands[artist] = Band()

    def add_song(self, sng):
        self.bands[sng.artist].all_songs.add(sng)
        if sng.is_cover():
            self.bands[sng.artist].all_covers.add(sng)
        else:
            self.bands[sng.artist].all_originals.add(sng)

    def songs_by_day(self):
        print("Songs by day statistics")
        song_counts_by_day = [0] * 7
        songs_by_day = [SongCont() for _ in range(7)]
        for band in self.bands.values():
            for song in band.all_songs.all:
                song_counts_by_day[song.get_weekday()] += 1
                songs_by_day[song.get_weekday()].add(song)
        print(", ".join(["{}: {}".format(day, songs) for day, songs in zip(calendar.day_name, song_counts_by_day)]))

        num_songs = sum(song_counts_by_day)
        songs_perc = []
        for sbd in song_counts_by_day:
            songs_perc.append(float(sbd) / float(num_songs))
        print(", ".join(["{}: {}".format(day, songs) for day, songs in zip(calendar.day_name, songs_perc)]))

        for songs, day in zip(songs_by_day, calendar.day_name):
            print("\n{}: {}\n".format(day, songs.sorted_list()[:20]))

        unique_num = 1
        while unique_num <= 256:
            self.unique_songs_by(unique_num, songs_by_day, calendar.day_name, "day")
            unique_num *= 2

    def songs_by_month(self):
        months = list(calendar.month_name)
        months.pop(0)

        print("\n\nSongs by month statistics")
        song_counts_by_month = [0] * 12
        songs_by_month = [SongCont() for _ in range(12)]
        for band in self.bands.values():
            for song in band.all_songs.all:
                song_counts_by_month[song.date.month - 1] += 1
                songs_by_month[song.date.month - 1].add(song)
        print(", ".join(["{}: {}".format(month, songs) for month, songs in zip(months, song_counts_by_month)]))

        num_songs = sum(song_counts_by_month)
        songs_perc = []
        for sbd in song_counts_by_month:
            songs_perc.append(float(sbd) / float(num_songs))
        print(", ".join(["{}: {}".format(month, songs) for month, songs in zip(months, songs_perc)]))

        for songs, month in zip(songs_by_month, months):
            print("\n{}: {}\n".format(month, songs.sorted_list()[:20]))

        unique_num = 1
        while unique_num <= 256:
            self.unique_songs_by(unique_num, songs_by_month, months, "month")
            unique_num *= 2

    def songs_by_year(self):
        years = [year+1965 for year in range(53)]
        print("\n\nSongs by year statistics")
        song_counts_by_year = [0] * 53
        songs_by_year = [SongCont() for _ in range(53)]
        for band in self.bands.values():
            for song in band.all_songs.all:
                song_counts_by_year[song.date.year - 1965] += 1
                songs_by_year[song.date.year - 1965].add(song)
        print(", ".join(["{}: {}".format(year, songs) for year, songs in zip(years, song_counts_by_year)]))

        num_songs = sum(song_counts_by_year)
        songs_perc = []
        for sbd in song_counts_by_year:
            songs_perc.append(float(sbd) / float(num_songs))
        print(", ".join(["{}: {}".format(year, songs) for year, songs in zip(years, songs_perc)]))

        for songs, year in zip(songs_by_year, years):
            print("\n{}: {}\n".format(year, songs.sorted_list()[:20]))

        unique_num = 1
        while unique_num <= 16:
            self.unique_songs_by(unique_num, songs_by_year, years, "year")
            unique_num *= 2
        
    def unique_songs_by(self, unique_num, songs_by, elems, print_id):
        songs_by_lists = []
        for songs in songs_by:
            songs_by_lists.append(songs.sorted_top_keys(unique_num))

        unique_songs = np.array(songs_by_lists)

        unique_songs = unique_songs.ravel()
        try:
            unique_songs_set = set(song for song in unique_songs if (unique_songs == song).sum() == 1)
        except AttributeError:
            pass

        unique_songs_by =[[] for _ in range(len(elems))]
        for uniqs in unique_songs_set:
            for i, sdb in enumerate(songs_by_lists):
                if uniqs in sdb:
                    unique_songs_by[i].append(uniqs)

        print("\nUnique songs by {} for top {}".format(print_id, unique_num))
        for uniqs, elem in zip(unique_songs_by, elems):
            if len(uniqs):
                print("{}: {}".format(elem, uniqs))

    def __str__(self):
        string = ""
        for key, val in self.bands.items():
            string += "{}{}\n\n".format(key, val)
        return string

    def __repr__(self):
        string = ""
        for key, val in self.bands.items():
            string += "{}{}\n\n".format(key, val)
        return string
        

class SongCont(object):
    def __init__(self):
        self.freq_dict = {}
        self.all = []

    def add(self, song):
        self.all.append(song)
        if song.name in self.freq_dict:
            old_val = self.freq_dict[song.name]
            self.freq_dict[song.name] = old_val + 1
        else:
            self.freq_dict[song.name] = 1

    def sorted_list(self):
        return [(key, self.freq_dict[key]) for key in sorted(self.freq_dict, key=self.freq_dict.get, reverse=True)]

    def sorted_top_keys(self, num):
        return [key[0] for key in self.sorted_list()[:num]]

    def keys_set(self):
        return set(self.freq_dict.keys())

    def __str__(self):
        return str(self.freq_dict)

    def __len__(self):
        return len(self.freq_dict)

    def __repr__(self):
        return str(self.freq_dict)
