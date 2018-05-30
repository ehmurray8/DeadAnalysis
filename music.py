from collections import defaultdict
from typing import Callable, List, Tuple, Dict
from functools import wraps
from song import Venue, Song, Tour, Concert
from map_helper import create_graph_code
from config import NUM_TOP_CONCERTS, NUM_TOP_ENCORES, NUM_TOP_SET_SONGS

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
        self.songs = {}  # type: Dict[str: Song]
        self.county_map_html = None  # type: str
        self.state_map_html = None  # type: str
        self.country_map_html = None  # type: str

    def get_maps(self):
        return create_graph_code(self)

    def start_year(self):
        return self.concerts[-1].date.year

    def last_year(self):
        return self.concerts[0].date.year

    def basic_concert_info(self):
        num_sets = []
        for concert in self.concerts:
            num_sets.append(len(concert.sets))
        usual_num_sets = max(set(num_sets), key=num_sets.count)
        set_lengths = [[] for _ in range(usual_num_sets)]
        encore_length = []
        sets = [defaultdict(int) for _ in range(usual_num_sets)]
        dates = [defaultdict(list) for _ in range(usual_num_sets)]
        encores = defaultdict(int)
        total_length = 0
        for concert in self.concerts:
            if len(concert.sets) == usual_num_sets:
                for i, s in enumerate(concert.sets):
                    set_lengths[i].append(len(s))
                    sets[i][s] += 1
                    dates[i][s] += [concert.date]
                    total_length += len(s)
            elif concert.sets is not None:
                total_length += sum(len(s) for s in concert.sets)

            if concert.encores is not None and len(concert.encores):
                encore_length.append(len(concert.encores))
                encores[concert.encores] += 1
                total_length += len(concert.encores)
            else:
                encore_length.append(0)

        common_sets = [[] for _ in range(usual_num_sets)]
        num_multiple_encores = 0
        num_solo_encore = 0
        num_multiple_sets = [0 for _ in range(usual_num_sets)]
        num_solo_sets = [0 for _ in range(usual_num_sets)]
        common_set_songs = [defaultdict(int) for _ in range(usual_num_sets)]
        for i, s in enumerate(sets):
            common_sets[i] = [(key, s[key]) for key in sorted(s, key=s.get, reverse=True)]
            for key, value in common_sets[i]:
                if value > 1:
                    num_multiple_sets[i] += 1
                else:
                    num_solo_sets[i] += 1
                for song in key:
                    common_set_songs[i][song] += 1
            common_sets[i] = common_sets[i][:NUM_TOP_CONCERTS]

        common_set_songs_ordered = [[] for _ in range(usual_num_sets)]
        uncommon_set_songs_ordered = [[] for _ in range(usual_num_sets)]
        for i, ss in enumerate(common_set_songs):
            common_set_songs_ordered[i] = [(key, ss[key])
                                           for key in sorted(ss, key=ss.get, reverse=True)][:NUM_TOP_SET_SONGS]
            uncommon_set_songs_ordered[i] = [(key, ss[key])
                                             for key in sorted(ss, key=ss.get, reverse=False)][:NUM_TOP_SET_SONGS]
        common_encores = [(key, encores[key]) for key in sorted(encores, key=encores.get, reverse=True)]
        uncommon_encores = [(key, encores[key]) for key in sorted(encores, key=encores.get, reverse=False)]
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
        return set_lengths, round(encore_length, 2), common_sets, common_encores[:NUM_TOP_ENCORES], num_solo_sets,\
               num_multiple_sets, num_solo_encore, num_multiple_encores, common_set_songs_ordered, top_set_dates,\
               uncommon_set_songs_ordered, uncommon_encores[:NUM_TOP_ENCORES], round(total_length/len(self.concerts), 2)

    def songs_by_day(self, select_num: int) -> Tuple[List[List[Tuple[str, float]]], List[float], List[float]]:
        """
        Return a list of lists for each day there is song data for and selects the top select_num for
        each day.

        :param select_num: the top number of songs to select by day
        :return: the top select_num song names by day
        """
        song_counts_by_day = [0] * 7
        songs_by_day = [SongCont() for _ in range(7)]
        for concert in self.concerts:
            song_counts_by_day[concert.get_weekday()] += 1
            for song in [song for s in concert.sets + [concert.encores] for song in s]:
                songs_by_day[concert.get_weekday()].add(song)

        num_songs = sum(song_counts_by_day)
        songs_perc = []
        songs_total = []
        for sbd in song_counts_by_day:
            songs_total.append(sbd)
            songs_perc.append(float(sbd) / float(num_songs))

        return unique_songs_by(select_num, songs_by_day), songs_perc, songs_total

    def songs_by_month(self, select_num: int) -> Tuple[List[List[Tuple[str, int]]], List[float], List[float]]:
        """
        Return a list of lists for each month there is song data for and selects the top select_num for
        each month.

        :param select_num: the top number of songs to select by month
        :return: the top select_num song names by month
        """
        song_counts_by_month = [0] * 12
        songs_by_month = [SongCont() for _ in range(12)]
        for concert in self.concerts:
            song_counts_by_month[concert.date.month - 1] += 1
            for song in [song for s in concert.sets + [concert.encores] for song in s]:
                songs_by_month[concert.date.month - 1].add(song)

        num_songs = sum(song_counts_by_month)
        songs_perc = []
        songs_total = []
        for sbd in song_counts_by_month:
            songs_total.append(sbd)
            songs_perc.append(float(sbd) / float(num_songs))

        return unique_songs_by(select_num, songs_by_month), songs_perc, songs_total

    def songs_by_year(self, select_num: int) -> Tuple[List[List[Tuple[str, float]]], List[float], List[float]]:
        """
        Return a list of lists for each year there is song data for and selects the top select_num for
        each year.

        :param select_num: the top number of songs to select by year
        :return: the top select_num song names by year
        """
        num_years = self.last_year() - self.start_year() + 1
        song_counts_by_year = [0] * num_years
        songs_by_year = [SongCont() for _ in range(num_years)]
        for concert in self.concerts:
            i = concert.date.year - self.start_year()
            song_counts_by_year[i] += 1
            for song in [song for s in concert.sets + [concert.encores] for song in s]:
                songs_by_year[i].add(song)

        num_songs = sum(song_counts_by_year)
        songs_perc = []
        songs_total = []
        for sbd in song_counts_by_year:
            songs_total.append(sbd)
            songs_perc.append(float(sbd) / float(num_songs))

        return unique_songs_by(select_num, songs_by_year), songs_perc, songs_total

    def top_songs(self, select_num: int):
        song_cont = SongCont()
        for concert in self.concerts:
            for song in [song for s in concert.sets + [concert.encores] for song in s]:
                song_cont.add(song)
        return song_cont.sorted_top_tuples(select_num)

    def all_song_info(self):
        song_cont = SongCont()
        for concert in self.concerts:
            for song in [song for s in concert.sets + [concert.encores] for song in s]:
                song_cont.add(song)
        return song_cont.all_songs(), song_cont.all_covered_songs(), song_cont.all_originals()

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


class SongCont(object):
    def __init__(self):
        self.freq_dict = defaultdict(int)
        self.all = []  # type: List[Song]

    def add(self, song: Song):
        self.all.append(song)
        self.freq_dict[song] += 1

    def sorted_list(self):
        return [(key, self.freq_dict[key]) for key in sorted(self.freq_dict, key=self.freq_dict.get, reverse=True)]

    def sorted_top_keys(self, num):
        return [key[0].name for key in self.sorted_list() if key[0].name != "" and key[0].name != "Drums"
                and key[0].name != "Space"][:num]

    def sorted_top_tuples(self, num):
        return [(key[0].name, key[1]) for key in self.sorted_list() if key[0].name != "" and key[0].name != "Drums"
                and key[0].name != "Space"][:num]

    def all_covered_songs(self):
        return ["{} ({}) - {}".format(key[0].name, key[0].orig_artist, key[1]) for key in self.sorted_list()
                if key[0].name != "" and key[0].name != "Drums" and key[0].name != "Space" and key[0].is_cover()]

    def all_songs(self):
        return ["{} - {}".format(key[0].name, key[1]) for key in self.sorted_list()
                if key[0].name != "" and key[0].name != "Drums" and key[0].name != "Space"]

    def all_originals(self):
        return ["{} - {}".format(key[0].name, key[1]) for key in self.sorted_list()
                if key[0].name != "" and key[0].name != "Drums" and key[0].name != "Space" and not key[0].is_cover()]

    def keys_set(self):
        return set(self.freq_dict.keys())

    def __str__(self):
        return str(self.freq_dict)

    def __len__(self):
        return len(self.freq_dict)

    def __repr__(self):
        return str(self.freq_dict)


def unique_songs_by(unique_num: int, songs_by: List[SongCont]) -> List[List[Tuple[str, int]]]:
    songs_by_lists = []
    for songs in songs_by:
        songs_by_lists.append(songs.sorted_top_tuples(unique_num))
    return [[(song, num) for song, num in song_list] for song_list in songs_by_lists]
