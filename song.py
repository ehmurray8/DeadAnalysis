import datetime
from typing import List, Optional


class Tour(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class Song(object):
    def __init__(self, artist: str, orig_artist: str, name: str):
        self.artist = artist
        self.orig_artist = orig_artist
        self.name = name

    def is_cover(self):
        return True if self.artist != self.orig_artist else False

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class Concert(object):
    def __init__(self, date: str, venue_id: str, sets: List[List[Song]], encores: List[Song], tour_id: Optional[Tour]):
        self.date = datetime.datetime.strptime(date, "%d-%m-%Y")
        self.venue_id = venue_id
        self.sets = sets
        self.encores = encores
        self.tour = tour_id

    def get_weekday(self):
        return self.date.weekday()

    def __repr__(self):
        return self.date

    def __str__(self):
        return self.date.strftime("%d-%m-%Y Show")

class Venue(object):
    def __init__(self, name: str, city: str, state: str, state_code: str, country: str, country_code: str,
                 latitude: str, longitude: str, fips: str):
        self.name = name
        self.city = city
        self.state = state
        self.state_code = state_code
        self.country = country
        self.country_code = country_code
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.fips = fips

    def __repr__(self):
        return self.name

    def __str__(self):
        return "{}, {}, {}".format(self.name, self.city, self.state_code)

