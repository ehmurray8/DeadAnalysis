import plotly.plotly as py
import plotly.figure_factory as ff
import get_song_data as gsd
from collections import defaultdict
import pycountry

if __name__ == "__main__":
    colorscale = ["#f7fbff", "#d2e3f3", "#9ecae1", "#57a0ce", "#2171b5", "#0b4083", "#08306b"]

    music = gsd.get_pickled_song_data()
    fips = music.song_fips()
    frequencies = defaultdict(int)
    for fip in fips:
        if fip != "NA":
            frequencies[fip] += 1

    sorted_concert_nums = list(sorted(frequencies.values()))
    length = len(sorted_concert_nums)
    size = 10
    bins = [sorted_concert_nums[i:i+int(length/size)] for i in range(0, length, int(length/size))]
    bins = [0] + [max(bin) for bin in bins]

    fig = ff.create_choropleth(
        fips=list(frequencies.keys()), values=list(frequencies.values()),
        binning_endpoints=bins, #  colorscale=colorscale,
        show_state_data=True, show_hover=True, centroid_marker={'opacity': 0}, asp=2.9,
        title='Grateful Dead Concerts by Location', legend_title='Number of Concerts' )
    py.iplot(fig, filename='Dead Shows (States)')

    frequencies = defaultdict(int)
    for fip in music.song_state_codes():
        frequencies[fip] += 1

    data = [dict(type='choropleth', # colorscale=scl,
            autocolorscale=True, locations=[loc[:2] for loc in frequencies.keys()], z=list(frequencies.values()),
            locationmode='USA-states', # text = df['text'],
            marker=dict(line=dict (color='rgb(255,255,255)', width=2)), colorbar=dict(title="Number of Concerts"))]

    layout = dict(title='Grateful Dead Concerts by State', geo=dict(scope='usa', projection=dict(type='albers usa'),
                  showlakes = True, lakecolor='rgb(255, 255, 255)'))

    fig = dict(data=data, layout=layout)
    py.iplot(fig, filename='Dead Shows by State')

    frequencies = defaultdict(int)
    for fip in music.song_country_codes():
        frequencies[fip] += 1

    data = [dict(type='choropleth',
                 locations=[pycountry.countries.get(alpha_2=code).alpha_3 for code in frequencies.keys()],
                 z = list(frequencies.values()),
                 text = [pycountry.countries.get(alpha_2=code).name for code in frequencies.keys()],
                 # colorscale = [[0,"rgb(5, 10, 172)"],[0.35,"rgb(40, 60, 190)"],[0.5,"rgb(70, 100, 245)"],\
                 #     [0.6,"rgb(90, 120, 245)"],[0.7,"rgb(106, 137, 247)"],[1,"rgb(220, 220, 220)"]],
                 autocolorscale=True, reversescale=True, marker=dict(line=dict(color='rgb(180,180,180)', width=0.5)),
                 colorbar = dict(autotick=False, title='Number of Shows'))]

    layout = dict(title='Grateful Dead Shows by Country', geo=dict(showframe=True, showcoastlines=True,
            projection = dict(type='Mercator')))

    fig = dict( data=data, layout=layout )
    py.iplot( fig, validate=False, filename='Grateful Dead Shows World' )
