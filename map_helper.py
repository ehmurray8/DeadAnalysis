from collections import defaultdict
from lxml.html import tostring
from lxml import html
import plotly.figure_factory as ff
import pycountry
from plotly import offline
from config import ARTIST
import os


def create_graph_code(music):
    fips = music.concerts_by_fips()
    frequencies = defaultdict(int)
    for fip in fips:
        if fip != "NA":
            frequencies[fip] += 1

    sorted_concert_nums = list(sorted(frequencies.values()))
    length = len(sorted_concert_nums)
    size = 5
    bins = [sorted_concert_nums[i:i+int(length/size)] for i in range(0, length, int(length/size))]
    bins = [1] + [max(bin) for bin in bins]
    bins = list(sorted(set(bins)))

    fig = ff.create_choropleth(fips=list(frequencies.keys()), values=list(frequencies.values()),
                               binning_endpoints=bins, #  colorscale=colorscale,
                               show_state_data=True, show_hover=True, centroid_marker={'opacity': 0}, asp=2.9,
                               title='{} Concerts by Location'.format(ARTIST), legend_title='Number of Concerts')
    plot_county = offline.plot(fig, filename=os.path.join("html", "_Maps", '{} Shows by County.html'.format(ARTIST)),
                               auto_open=False, show_link=False, config={'displayModeBar': False})
    plot_county = plot_county[7:]
    root = html.parse(plot_county).getroot()
    plot_county_code = tostring(root.getchildren()[1])
    plot_county_code = plot_county_code.decode("utf-8").replace("<body>", '<div align="center">').replace("</body>", "</div>")

    frequencies = defaultdict(int)
    for code in music.concerts_by_state_codes():
        frequencies[code] += 1

    data = [dict(type='choropleth', autocolorscale=True,
                 locations=[loc[:2] for loc in frequencies.keys()], z=list(frequencies.values()),
                 locationmode='USA-states', # text = df['text'],
                 marker=dict(line=dict(color='rgb(180,180,180)', width=2)), colorbar=dict(title="Number of Concerts"))]

    layout = dict(title='{} Concerts by State'.format(ARTIST),
                  geo=dict(scope='usa', projection=dict(type='albers usa'), showlakes=True,
                           lakecolor='rgb(255, 255, 255)'), width=1200, height=800)

    fig = dict(data=data, layout=layout)
    plot_state = offline.plot(fig, filename=os.path.join("html", "_Maps", '{} Shows by State.html'.format(ARTIST)),
                              auto_open=False, show_link=False, config={'displayModeBar': False})

    plot_state = plot_state[7:]
    root = html.parse(plot_state).getroot()
    plot_state_code = tostring(root.getchildren()[1]).decode("utf-8")
    plot_state_code = plot_state_code.replace("<body>", '<div align="center">').replace("</body>", "</div>")

    frequencies = defaultdict(int)
    for code in music.concerts_by_country_codes():
        frequencies[code] += 1

    data = [dict(type='choropleth',
                 locations=[pycountry.countries.get(alpha_2=code).alpha_3 for code in frequencies.keys()],
                 z = list(frequencies.values()),
                 text = [pycountry.countries.get(alpha_2=code).name for code in frequencies.keys()],
                 autocolorscale=True, marker=dict(line=dict(color='rgb(180,180,180)', width=0.5)),
                 colorbar = dict(autotick=False, title='Number of Shows'))]

    layout = dict(title='{} Shows by Country'.format(ARTIST), geo=dict(showframe=True, showcoastlines=True,
                  projection=dict(type='Mercator')), width=1200, height=800)

    fig = dict(data=data, layout=layout)
    plot_world = offline.plot(fig, validate=False, filename=os.path.join("html", "_Maps",
                                                                         '{} Shows World.html'.format(ARTIST)),
                              auto_open=False, show_link=False, config={'displayModeBar': False})

    plot_world = plot_world[7:]
    root = html.parse(plot_world).getroot()
    plot_world_code = tostring(root.getchildren()[1]).decode("utf-8")
    plot_world_code = plot_world_code.replace("<body>", '<div align="center">').replace("</body>", "</div>")
    return plot_county_code, plot_state_code, plot_world_code
