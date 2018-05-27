from collections import defaultdict
import calendar
from typing import Callable, List, Tuple, Dict
from functools import wraps
from song import Venue, Song, Tour, Concert
from config import START_YEAR

def concerts_by(function: Callable) -> Callable:
    @wraps(function)
    def wrapper(self) -> List:
        locs = []
        for concert in self.concerts:
            function(self, locs, concert)
        return locs
    return wrapper


class MusicData(object):
    def __init__(self):
        self.venues = {}  # type: Dict[str: Venue]
        self.tours = []  # type: List[Tour]
        self.concerts = []  # type: List[Concert]

    def songs_by_day(self, select_num: int) -> Tuple[List[List[str]], List[float]]:
        """
        Return a list of lists for each day there is song data for and selects the top select_num for
        each day.

        :param select_num: the top number of songs to select by day
        :return: the top select_num song names by day
        """
        song_counts_by_day = [0] * 7
        songs_by_day = [SongCont() for _ in range(7)]
        for concert in self.concerts:
            song_counts_by_day[concert.get_weekday()] += sum([len(s) for s in concert.sets]) + len(concert.encores)
            for song in [song for s in concert.sets + [concert.encores] for song in s]:
                songs_by_day[concert.get_weekday()].add(song)

        num_songs = sum(song_counts_by_day)
        songs_perc = []
        for sbd in song_counts_by_day:
            songs_perc.append(float(sbd) / float(num_songs))

        return unique_songs_by(select_num, songs_by_day, calendar.day_name), songs_perc

    def songs_by_month(self, select_num: int) -> Tuple[List[List[str]], List[float]]:
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
        for concert in self.concerts:
            song_counts_by_month[concert.date.month - 1] += sum([len(s) for s in concert.sets]) + len(concert.encores)
            for song in [song for s in concert.sets + [concert.encores] for song in s]:
                songs_by_month[concert.date.month - 1].add(song)

        num_songs = sum(song_counts_by_month)
        songs_perc = []
        for sbd in song_counts_by_month:
            songs_perc.append(float(sbd) / float(num_songs))

        return unique_songs_by(select_num, songs_by_month, months), songs_perc

    def songs_by_year(self, select_num: int) -> Tuple[List[List[str]], List[float]]:
        """
        Return a list of lists for each year there is song data for and selects the top select_num for
        each year.

        :param select_num: the top number of songs to select by year
        :return: the top select_num song names by year
        """
        years = [year+START_YEAR for year in range(53)]
        song_counts_by_year = [0] * 53
        songs_by_year = [SongCont() for _ in range(53)]
        for concert in self.concerts:
            song_counts_by_year[concert.date.year - START_YEAR] += sum([len(s) for s in concert.sets]) + \
                                                                   len(concert.encores)
            for song in [song for s in concert.sets + [concert.encores] for song in s]:
                songs_by_year[concert.date.year - START_YEAR].add(song)

        num_songs = sum(song_counts_by_year)
        songs_perc = []
        for sbd in song_counts_by_year:
            songs_perc.append(float(sbd) / float(num_songs))

        return unique_songs_by(select_num, songs_by_year, years), songs_perc

    def top_songs(self, select_num: int):
        song_cont = SongCont()
        for concert in self.concerts:
            for song in [song for s in concert.sets + [concert.encores] for song in s]:
                song_cont.add(song)
        return song_cont.sorted_top_keys(select_num)

    @concerts_by
    def concerts_by_location(self, coordinates: List[Tuple[float, float]], concert: Concert):
        """
        Returns all the latitude, longitude for all songs played by the specified artists.

        :param coordinates: list of latitude, longitude tuples for all songs played
        :param song: the song to add to the list
        :return: the latitude, longitude pair tuples for all songs played
        """
        venue = self.venues[concert.venue_id]
        coordinates.append((venue.latitude, venue.longitude))

    @concerts_by
    def concerts_by_fips(self, fips: List[str], concert: Concert):
        """
        Returns all the fips code for all songs played by the specified artists.

        :param fips: list of fips strings for all songs played
        :param song: the song to add to the list
        :return: the fips strings for all songs played
        """
        fips.append(self.venues[concert.venue_id].fips)

    @concerts_by
    def concerts_by_state_codes(self, codes: List[str], concert: Concert):
        """
        Returns all the state codes for all songs played by the specified artists.

        :param codes: list of state code strings for all songs played
        :param song: the song to add to the list
        :return: the state code strings for all songs played
        """
        codes.append(self.venues[concert.venue_id].state_code)

    @concerts_by
    def concerts_by_country_codes(self, codes: List[str], concert: Concert):
        """
        Returns all the country codes for all songs played by the specified artists.

        :param codes: list of country code strings for all songs played
        :param song: the country to add to the list
        :return: the country code strings for all songs played
        """
        codes.append(self.venues[concert.venue_id].country_code)


class SongCont(object):
    def __init__(self):
        self.freq_dict = defaultdict(int)
        self.all = []  # type: List[Song]

    def add(self, song: Song):
        self.all.append(song)
        self.freq_dict[song.name] += 1

    def sorted_list(self):
        return [(key, self.freq_dict[key]) for key in sorted(self.freq_dict, key=self.freq_dict.get, reverse=True)]

    def sorted_top_keys(self, num):
        return [key[0] for key in self.sorted_list() if key[0] != ""][:num]

    def keys_set(self):
        return set(self.freq_dict.keys())

    def __str__(self):
        return str(self.freq_dict)

    def __len__(self):
        return len(self.freq_dict)

    def __repr__(self):
        return str(self.freq_dict)


def unique_songs_by(unique_num: int, songs_by: List[SongCont], elems: List) -> List[List[str]]:
    songs_by_lists = []
    for songs in songs_by:
        songs_by_lists.append(songs.sorted_top_keys(unique_num))

    unique_songs = [song for song_list in songs_by_lists for song in song_list]

    unique_songs_set = set(unique_songs)
    unique_songs_list = [[] for _ in range(len(elems))]
    for uniqs in unique_songs_set:
        for i, sdb in enumerate(songs_by_lists):
            if uniqs in sdb:
                unique_songs_list[i].append(uniqs)
    return [[song for song in song_list if song != ""] for song_list in songs_by_lists]
