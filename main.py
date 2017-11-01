import get_song_data as gsd

if __name__ == "__main__":
    #gsd.get_song_data()
    music = gsd.get_pickled_song_data()
    print(music)
    music.songs_by_day()
    music.songs_by_month()
    music.songs_by_year()
