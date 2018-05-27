import calendar
import datetime
import numpy as np
from collections import OrderedDict
from config import ARTISTS, SELECTED_COVERS
from typing import List, Dict, Optional, Tuple, Callable
from functools import wraps


class Concert(object):
    def __init__(self):
        pass


class Location(object):
    def __init__(self, city: str, state: str, state_code: str, country: str, country_code: str, venue: str,
                 coordinates: Dict[str, str], fips: int):
        self.city = city
        self.state = state
        self.state_code = state_code
        self.country = country
        self.country_code = country_code
        self.venue = venue
        self.latitude = float(coordinates["lat"])
        self.longitude = float(coordinates["long"])
        self.fips = fips


class Song(object):
    def __init__(self, loc: Location, date: str, tour: str, artist: str, orig_artist: str, name: str):
        self.location = loc
        self.date = datetime.datetime.strptime(date, "%d-%m-%Y").date()
        self.artist = artist
        self.orig_artist = orig_artist
        self.name = name
        self.tour = tour

    def get_weekday(self):
        return self.date.weekday()

    def is_cover(self):
        return True if self.artist != self.orig_artist else False

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


def songs_by(function: Callable) -> Callable:
    @wraps(function)
    def wrapper(self, artists: Optional[List[str]]=None) -> List:
        bands = [band for artist, band in self.bands.items() if artists is None or artist in artists]
        coordinates = []
        for band in bands:
            for song in band.all_songs.all:
                function(self, coordinates, song)
        return coordinates
    return wrapper


class MusicData(object):
    def __init__(self):
        self.bands = OrderedDict()
        for artist in ARTISTS:
            self.bands[artist] = Band()

    def add_song(self, song: Song):
        """
        Adds a song to the correct entry of the bands dictionary.

        :param song: the song to add
        """
        self.bands[song.artist].add_song(song)

    def songs_by_day(self, select_num: int) -> List[List[str]]:
        """
        Return a list of lists for each day there is song data for and selects the top select_num for
        each day.

        :param select_num: the top number of songs to select by day
        :return: the top select_num song names by day
        """
        song_counts_by_day = [0] * 7
        songs_by_day = [SongCont() for _ in range(7)]
        for band in self.bands.values():
            for song in band.all_songs.all:
                song_counts_by_day[song.get_weekday()] += 1
                songs_by_day[song.get_weekday()].add(song)

        num_songs = sum(song_counts_by_day)
        songs_perc = []
        for sbd in song_counts_by_day:
            songs_perc.append(float(sbd) / float(num_songs))

        return unique_songs_by(select_num, songs_by_day, calendar.day_name)

    def songs_by_month(self, select_num: int) -> List[List[str]]:
        """
        Return a list of lists for each month there is song data for and selects the top select_num for
        each month.

        :param select_num: the top number of songs to select by month
        :return: the top select_num song names by month
        """
        months = list(calendar.month_name)
        months.pop(0)

        song_counts_by_month = [0] * 12
        songs_by_month = [SongCont() for _ in range(12)]
        for band in self.bands.values():
            for song in band.all_songs.all:
                song_counts_by_month[song.date.month - 1] += 1
                songs_by_month[song.date.month - 1].add(song)

        num_songs = sum(song_counts_by_month)
        songs_perc = []
        for sbd in song_counts_by_month:
            songs_perc.append(float(sbd) / float(num_songs))

        return unique_songs_by(select_num, songs_by_month, months)

    def songs_by_year(self, select_num: int) -> List[List[str]]:
        """
        Return a list of lists for each year there is song data for and selects the top select_num for
        each year.

        :param select_num: the top number of songs to select by year
        :return: the top select_num song names by year
        """
        years = [year+1965 for year in range(53)]
        song_counts_by_year = [0] * 53
        songs_by_year = [SongCont() for _ in range(53)]
        for band in self.bands.values():
            for song in band.all_songs.all:
                song_counts_by_year[song.date.year - 1965] += 1
                songs_by_year[song.date.year - 1965].add(song)

        num_songs = sum(song_counts_by_year)
        songs_perc = []
        for sbd in song_counts_by_year:
            songs_perc.append(float(sbd) / float(num_songs))

        return unique_songs_by(select_num, songs_by_year, years)

    @songs_by
    def songs_by_location(self, coordinates: List[Tuple[float, float]], song: Song):
        """
        Returns all the latitude, longitude for all songs played by the specified artists.

        :param coordinates: list of latitude, longitude tuples for all songs played
        :param song: the song to add to the list
        :return: the latitude, longitude pair tuples for all songs played
        """
        coordinates.append((song.location.latitude, song.location.longitude))

    @songs_by
    def song_fips(self, fips: List[str], song: Song):
        """
        Returns all the fips code for all songs played by the specified artists.

        :param fips: list of fips strings for all songs played
        :param song: the song to add to the list
        :return: the fips strings for all songs played
        """
        fips.append(song.location.fips)

    @songs_by
    def song_state_codes(self, codes: List[str], song: Song):
        """
        Returns all the state codes for all songs played by the specified artists.

        :param codes: list of state code strings for all songs played
        :param song: the song to add to the list
        :return: the state code strings for all songs played
        """
        codes.append(song.location.state_code)

    @songs_by
    def song_country_codes(self, codes: List[str], song: Song):
        """
        Returns all the country codes for all songs played by the specified artists.

        :param codes: list of country code strings for all songs played
        :param song: the country to add to the list
        :return: the country code strings for all songs played
        """
        codes.append(song.location.country_code)

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
        self.all = []  # type: List[Song]

    def add(self, song: Song):
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


class Band(object):
    def __init__(self):
        self.all_songs = SongCont()
        self.all_covers = SongCont()
        self.all_originals = SongCont()

    def add_song(self, song: Song):
        self.all_songs.add(song)
        self.all_covers.add(song) if song.is_cover() else self.all_originals.add(song)

    def num_covers(self):
        return len(self.all_covers)

    def num_songs(self):
        return len(self.all_songs)

    def num_originals(self):
        return len(self.all_originals)

    def selected_cover_songs(self) -> List[SongCont]:
        chosen_covers = [SongCont() for _ in range(len(SELECTED_COVERS))]
        for artist, cc in zip(SELECTED_COVERS, chosen_covers):
            for cover in self.all_covers.all:
                if cover.orig_artist == artist:
                    cc.add(cover)
        return chosen_covers


def unique_songs_by(unique_num: int, songs_by: List[SongCont], elems: List) -> List[List[str]]:
    songs_by_lists = []
    for songs in songs_by:
        songs_by_lists.append(songs.sorted_top_keys(unique_num))

    unique_songs = np.array(songs_by_lists)
    unique_songs = unique_songs.ravel()

    unique_songs_set = set(unique_songs)
    unique_songs_list = [[] for _ in range(len(elems))]
    for uniqs in unique_songs_set:
        for i, sdb in enumerate(songs_by_lists):
            if uniqs in sdb:
                unique_songs_list[i].append(uniqs)
    return songs_by_lists
