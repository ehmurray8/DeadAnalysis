import plotly.plotly as py
import plotly.figure_factory as ff
from geopandas import GeoDataFrame
import geopandas
import get_song_data as gsd
from collections import defaultdict
import pycountry
from config import ARTIST


def create_graph_code():
    colorscale = ["#f7fbff", "#d2e3f3", "#9ecae1", "#57a0ce", "#2171b5", "#0b4083", "#08306b"]

    music = gsd.get_pickled_song_data()
    fips = music.concerts_by_fips()
    frequencies = defaultdict(int)
    for fip in fips:
        if fip != "NA":
            frequencies[fip] += 1

    sorted_concert_nums = list(sorted(frequencies.values()))
    length = len(sorted_concert_nums)
    size = 5
    bins = [sorted_concert_nums[i:i+int(length/size)] for i in range(0, length, int(length/size))]
    bins = [0] + [max(bin) for bin in bins]
    bins = list(sorted(set(bins)))

    fig = ff.create_choropleth(fips=list(frequencies.keys()), values=list(frequencies.values()),
                               binning_endpoints=bins, #  colorscale=colorscale,
                               show_state_data=True, show_hover=True, centroid_marker={'opacity': 0}, asp=2.9,
                               title='{} Concerts by Location'.format(ARTIST), legend_title='Number of Concerts')
    plot_county = py.iplot(fig, filename='{} Shows by County'.format(ARTIST))

    frequencies = defaultdict(int)
    for code in music.concerts_by_state_codes():
        frequencies[code] += 1

    data = [dict(type='choropleth', autocolorscale=True,
                 locations=[loc[:2] for loc in frequencies.keys()], z=list(frequencies.values()),
                 locationmode='USA-states', # text = df['text'],
                 marker=dict(line=dict (color='rgb(255,255,255)', width=2)), colorbar=dict(title="Number of Concerts"))]

    layout = dict(title='{} Concerts by State'.format(ARTIST), geo=dict(scope='usa', projection=dict(type='albers usa'),
                                                                    showlakes = True, lakecolor='rgb(255, 255, 255)'))

    fig = dict(data=data, layout=layout)
    plot_state = py.iplot(fig, filename='{} Shows by State'.format(ARTIST))

    frequencies = defaultdict(int)
    for code in music.concerts_by_country_codes():
        frequencies[code] += 1

    data = [dict(type='choropleth',
                 locations=[pycountry.countries.get(alpha_2=code).alpha_3 for code in frequencies.keys()],
                 z = list(frequencies.values()),
                 text = [pycountry.countries.get(alpha_2=code).name for code in frequencies.keys()],
                 autocolorscale=True, reversescale=True, marker=dict(line=dict(color='rgb(180,180,180)', width=0.5)),
                 colorbar = dict(autotick=False, title='Number of Shows'))]

    layout = dict(title='{} Shows by Country'.format(ARTIST), geo=dict(showframe=True, showcoastlines=True,
                                                                   projection = dict(type='Mercator')))

    fig = dict(data=data, layout=layout)
    plot_world = py.iplot(fig, validate=False, filename='{} Shows World'.format(ARTIST))
    return plot_county.embed_code, plot_state.embed_code, plot_world.embed_code


if __name__ == "__main__":
    create_graph_code()
