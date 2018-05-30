from collections import defaultdict
from typing import Callable, List, Tuple, Dict
from functools import wraps
from song import Venue, Song, Tour, Concert
from map_helper import create_graph_code
from config import FILTER_SONGS, NUM_TOP_COVERS


def concerts_by(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(self) -> List:
        locs = []
        for concert in self.concerts:
            func(self, locs, concert)
        return locs
    return wrapper

def songs_by(num):
    def _songs_by(func: Callable):
        @wraps(func)
        def wrapper(self: "MusicData", select_num: int) -> \
                Tuple[List[List[Tuple[str, float]]], List[float], List[float], List[int]]:
            number = num
            if number is None:
                number = self.last_year() - self.start_year() + 1
            concert_counts = [0] * number
            songs_by = [SongCont(FILTER_SONGS) for _ in range(number)]
            for concert in self.concerts:
                func(self, concert, concert_counts, songs_by)

            songs_perc = []
            songs_total = []
            for sbd in concert_counts:
                songs_total.append(sbd)
                songs_perc.append(sbd / sum(concert_counts))

            uniques = unique_songs_by(select_num, songs_by)
            idxs = [i for i, st in enumerate(songs_total) if not st]
            ret_idxs = [i for i, st in enumerate(songs_total) if st]
            songs_total = [x for x in songs_total if x]
            for i in reversed(idxs):
                del uniques[i]
                del songs_perc[i]
            return uniques, songs_perc, songs_total, ret_idxs
        return wrapper
    return _songs_by


class FrequencyDict(object):
    def __init__(self):
        self.freq_dict = defaultdict(int)

    def add(self, song, num=1):
        self.freq_dict[song] += num

    def sorted_list(self, descending):
        return [(key, self.freq_dict[key]) for key in sorted(self.freq_dict, key=self.freq_dict.get, reverse=descending)]

    def sorted_top_keys(self, num=None, descending=True):
        if num is None:
            num = len(self.freq_dict)
        return [key[0] for key in self.sorted_list(descending)][:num]

    def sorted_top_tuples(self, num=None, descending=True):
        if num is None:
            num = len(self.freq_dict)
        return [(key[0], key[1]) for key in self.sorted_list(descending)][:num]

    def keys_set(self):
        return set(self.freq_dict.keys())

    def __iter__(self):
        return ((key, value) for key, value in self.freq_dict.items())

    def __delitem__(self, key):
        del self.freq_dict[key]

    def __getitem__(self, key):
        return self.freq_dict[key]

    def __setitem__(self, key, value):
        self.freq_dict[key] = value

    def __str__(self):
        return str(self.freq_dict)

    def __len__(self):
        return len(self.freq_dict)

    def __repr__(self):
        return str(self.freq_dict)


class SongCont(FrequencyDict):
    def __init__(self, filter_songs: List[str]=list()):
        super().__init__()
        filter_songs.append("")
        self.filter_songs = filter_songs

    def sorted_top_keys(self, num=None, descending=True):
        if num is None:
            num = len(self.freq_dict)
        return [key[0].name for key in self.sorted_list(descending)
                if key[0].name not in self.filter_songs][:num]

    def sorted_top_tuples(self, num=None, descending=True):
        if num is None:
            num = len(self.freq_dict)
        return [(key[0].name, key[1]) for key in self.sorted_list(descending)
                if key[0].name not in self.filter_songs][:num]

    def all_covered_songs(self):
        return ["{} ({}) - {}".format(key[0].name, key[0].orig_artist, key[1]) for key in self.sorted_list(True)
                if key[0].name not in self.filter_songs and key[0].is_cover()]

    def all_songs(self):
        return ["{} - {}".format(key[0].name, key[1]) for key in self.sorted_list(True)
                if key[0].name not in self.filter_songs]

    def all_originals(self):
        return ["{} - {}".format(key[0].name, key[1]) for key in self.sorted_list(True)
                if key[0].name not in self.filter_songs and not key[0].is_cover()]


class MusicData(object):
    def __init__(self):
        self.venues = {}  # type: Dict[str: Venue]
        self.tours = []  # type: List[Tour]
        self.concerts = []  # type: List[Concert]
        self.songs = {}  # type: Dict[str: Song]

    def get_maps(self):
        return create_graph_code(self)

    def start_year(self):
        return self.concerts[-1].date.year

    def last_year(self):
        return self.concerts[0].date.year

    def cover_info(self):
        cover_artist_frequencies = FrequencyDict()
        cover_song_frequencies = SongCont(FILTER_SONGS)
        artist_to_song = defaultdict(list)
        total_cover_plays = 0
        for concert in self.concerts:
            for song in concert.all_songs():
                if song.is_cover():
                    cover_artist_frequencies.add(song.orig_artist)
                    cover_song_frequencies.add(song)
                    artist_to_song[song.orig_artist] += [song]
                    total_cover_plays += 1
        top_cover_artists = cover_artist_frequencies.sorted_top_tuples(num=NUM_TOP_COVERS)
        for artist, songs in artist_to_song.items():
            song_freqs = []
            for song in set(songs):
                song_freqs.append((song, cover_song_frequencies[song]))
            artist_to_song[artist] = list(reversed(sorted(song_freqs, key=lambda x: x[1])))
        return top_cover_artists, total_cover_plays, artist_to_song, len(cover_artist_frequencies)

    def tour_info(self):
        pass

    def venue_info(self):
        pass

    def basic_concert_info(self):
        num_sets = []
        for concert in self.concerts:
            num_sets.append(len(concert.sets))
        usual_num_sets = max(set(num_sets), key=num_sets.count)
        set_lengths = [[] for _ in range(usual_num_sets)]
        encore_length = []
        sets = [FrequencyDict() for _ in range(usual_num_sets)]
        dates = [defaultdict(list) for _ in range(usual_num_sets)]
        encores = FrequencyDict()
        total_length = 0
        covers_per_concert = 0
        for concert in self.concerts:
            if len(concert.sets) == usual_num_sets:
                for i, s in enumerate(concert.sets):
                    set_lengths[i].append(len(s))
                    sets[i].add(s)
                    dates[i][s] += [concert.date]
                    total_length += len(s)
            elif concert.sets is not None:
                total_length += sum(len(s) for s in concert.sets)

            if concert.encores is not None and len(concert.encores):
                encore_length.append(len(concert.encores))
                encores.add(concert.encores)
                total_length += len(concert.encores)
            else:
                encore_length.append(0)
            for s in concert.all_songs():
                if s.is_cover():
                    covers_per_concert += 1

        common_sets = [[] for _ in range(usual_num_sets)]
        num_multiple_encores = 0
        num_solo_encore = 0
        num_multiple_sets = [0 for _ in range(usual_num_sets)]
        num_solo_sets = [0 for _ in range(usual_num_sets)]
        common_set_songs = [FrequencyDict() for _ in range(usual_num_sets)]
        for i, s in enumerate(sets):
            common_sets[i] = s.sorted_top_tuples()
            for key, value in common_sets[i]:
                if value > 1:
                    num_multiple_sets[i] += 1
                else:
                    num_solo_sets[i] += 1
                for song in key:
                    common_set_songs[i].add(song)
            common_sets[i] = common_sets[i]

        common_set_songs_ordered = [[] for _ in range(usual_num_sets)]
        for i, ss in enumerate(common_set_songs):
            common_set_songs_ordered[i] = ss.sorted_top_tuples()
        common_encores = encores.sorted_top_tuples()
        for key, value in common_encores:
            if value > 1:
                num_multiple_encores += 1
            else:
                num_solo_encore += 1

        set_lengths = [round(sum(sl)/len(sl), 2) for sl in set_lengths]
        encore_length = sum(encore_length)/len(encore_length)
        top_set_dates = [[] for _ in range(usual_num_sets)]
        for i, cs in enumerate(common_sets):
            for c in cs:
                top_set_dates[i].append([date.strftime("%B %d, %Y") for date in sorted(dates[i][c[0]])])
        return set_lengths, round(encore_length, 2), common_sets, common_encores, num_solo_sets,\
               num_multiple_sets, num_solo_encore, num_multiple_encores, common_set_songs_ordered, top_set_dates,\
               round(total_length/len(self.concerts), 2),\
               round(covers_per_concert/len(self.concerts), 2)

    @songs_by(7)
    def songs_by_day(self, concert, concert_counts, songs_by_day):
        """
        Return a list of lists for each day there is song data for and selects the top select_num for
        each day.

        :param select_num: the top number of songs to select by day
        :return: the top select_num song names by day
        """
        concert_counts[concert.get_weekday()] += 1
        for song in concert.all_songs():
            songs_by_day[concert.get_weekday()].add(song)

    @songs_by(12)
    def songs_by_month(self, concert: Concert, concert_counts: List[int], songs_by_month: List["FrequencyDict"]):
        """
        Return a list of lists for each month there is song data for and selects the top select_num for
        each month.

        :param select_num: the top number of songs to select by month
        :return: the top select_num song names by month
        """
        concert_counts[concert.date.month - 1] += 1
        for song in concert.all_songs():
            songs_by_month[concert.date.month - 1].add(song)

    @songs_by(None)
    def songs_by_year(self, concert, concert_counts, songs_by_year):
        """
        Return a list of lists for each year there is song data for and selects the top select_num for
        each year.

        :param select_num: the top number of songs to select by year
        :return: the top select_num song names by year
        """
        i = concert.date.year - self.start_year()
        concert_counts[i] += 1
        for song in concert.all_songs():
            songs_by_year[i].add(song)

    def top_songs(self, select_num: int):
        song_cont = SongCont(FILTER_SONGS)
        for concert in self.concerts:
            for song in concert.all_songs():
                song_cont.add(song)
        return song_cont.sorted_top_tuples(select_num)

    def all_song_info(self):
        song_cont = SongCont()
        for concert in self.concerts:
            for song in concert.all_songs():
                song_cont.add(song)
        total_num_songs = sum(num for _, num in song_cont)
        return song_cont.all_songs(), song_cont.all_covered_songs(), song_cont.all_originals(), total_num_songs

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
    def concerts_by_states(self, codes, concert: Concert):
        codes.append(self.venues[concert.venue_id].state)

    @concerts_by
    def concerts_by_country_codes(self, codes: List[str], concert: Concert):
        """
        Returns all the country codes for all songs played by the specified artists.

        :param codes: list of country code strings for all songs played
        :param song: the country to add to the list
        :return: the country code strings for all songs played
        """
        codes.append(self.venues[concert.venue_id].country_code)


def unique_songs_by(unique_num: int, songs_by: List[FrequencyDict]) -> List[List[Tuple[str, int]]]:
    songs_by_lists = []
    for songs in songs_by:
        songs_by_lists.append(songs.sorted_top_tuples(unique_num))
    return [[(song, num) for song, num in song_list] for song_list in songs_by_lists]
