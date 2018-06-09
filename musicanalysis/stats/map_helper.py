from collections import defaultdict
from typing import List
from lxml.html import tostring
from lxml import html
import plotly.figure_factory as ff
import pycountry
from plotly import offline
import os
from .models import Concert


def get_plot(path: str, margin_bottom: int=0):
    plot = path[7:]
    root = html.parse(plot).getroot()
    plot_code = tostring(root.getchildren()[1])
    plot_code = plot_code.decode("utf-8").replace("<body>", '<div align="center" style="margin-bottom: {}px;">'
                                                  .format(margin_bottom)).replace("</body>", "</div>")
    os.remove(plot)
    return plot_code


def create_frequency_dict(values: List):
    frequencies = defaultdict(int)
    for val in values:
        frequencies[val] += 1
    return frequencies


def create_graph_code(artist: str):
    concerts = Concert.objects.filter(artist__name=artist).all()
    fips = [concert.venue.fips for concert in concerts if concert.venue.fips != "NA"]
    state_codes = [concert.venue.state_code for concert in concerts]
    country_codes = [concert.venue.country_code for concert in concerts]

    frequencies = create_frequency_dict([fip for fip in fips])
    sorted_concert_nums = list(sorted(frequencies.values()))
    length = len(sorted_concert_nums)
    size = 5
    bins = [sorted_concert_nums[i:i+int(length/size)] for i in range(0, length, int(length/size))]
    bins = [max(bin) if max(bin) else 1 for bin in bins]
    bins = list(sorted(set(bins)))
    colorscale = ["#c1c4c9", "#95979b", "#769ae0", "#3765bf", "#0c44b5", "#001744", "#0c44b5", "#1f4ea8", "#003296"]
    fig = ff.create_choropleth(fips=list(frequencies.keys()), values=list(frequencies.values()),
                               binning_endpoints=bins,
                               show_state_data=True, show_hover=True, centroid_marker={'opacity': 0}, asp=2.9,
                               title='', legend_title='Number of Concerts',
                               state_outline={'color': 'rgb(0,0,0)', 'width': 0.5},
                               colorscale=colorscale)

    if fig["data"][0]["name"] == "< 1":
        fig["data"][0]["name"] = 1

    plot_county = offline.plot(fig, filename=os.path.join('{} Shows by County.html'.format(artist)),
                               auto_open=False, show_link=False, config={'displayModeBar': False})
    plot_county_code = get_plot(plot_county, 100)

    frequencies = create_frequency_dict(state_codes)
    data = [dict(type='choropleth', autocolorscale=False,
                 locations=[loc[:2] for loc in frequencies.keys()], z=list(frequencies.values()),
                 locationmode='USA-states',
                 marker=dict(line=dict(color='rgb(180,180,180)', width=2)), colorbar=dict(title="Number of Concerts"),
                 reversescale=True,
                 colorscale=[[0,"rgb(5, 10, 172)"],[0.75,"rgb(20, 30, 180)"],[0.75,"rgb(40, 60, 190)"],[0.9,"rgb(70, 100, 245)"],
                               [0.95,"rgb(90, 120, 245)"],[0.99,"rgb(106, 137, 247)"],[1,"rgb(220, 220, 220)"]],)]
    layout = dict(title='', xaxis=dict(fixedrange=True),
                  yaxis=dict(autorange='reversed', fixedrange=True),
                  geo=dict(scope='usa', projection=dict(type='albers usa'), showlakes=True,
                  lakecolor='rgb(255, 255, 255)'), width=1200, height=800, dragmode='select', paper_bgcolor='rgba(0,0,0,0)',
                  plot_bgcolor='rgba(0,0,0,0)',)
    fig = dict(data=data, layout=layout)
    plot_state = offline.plot(fig, filename=os.path.join('{} Shows by State.html'.format(artist)),
                              auto_open=False, show_link=False, config={'displayModeBar': False})
    plot_state_code = get_plot(plot_state)

    frequencies = create_frequency_dict(country_codes)
    data = [dict(type='choropleth',
                 locations=[pycountry.countries.get(alpha_2=code).alpha_3 for code in frequencies.keys()],
                 z = list(frequencies.values()),
                 text = [pycountry.countries.get(alpha_2=code).name for code in frequencies.keys()],
                 autocolorscale=False, marker=dict(line=dict(color='rgb(180,180,180)', width=0.5)),
                 colorbar = dict(autotick=False, title='Number of Concerts'), reversescale=True,
                 colorscale = [[0,"rgb(5, 10, 172)"],[0.75,"rgb(20, 30, 180)"],[0.75,"rgb(40, 60, 190)"],[0.9,"rgb(70, 100, 245)"],
                               [0.95,"rgb(90, 120, 245)"],[0.99,"rgb(106, 137, 247)"],[1,"rgb(220, 220, 220)"]],)]

    layout = dict(title='', geo=dict(showframe=True, showcoastlines=True,
                  xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True), dragmode=False,
                  projection=dict(type='Mercator')), width=1200, height=800, paper_bgcolor='rgba(0,0,0,0)',
                  plot_bgcolor='rgba(0,0,0,0)', dragmode='select')
    fig = dict(data=data, layout=layout)
    plot_world = offline.plot(fig, validate=False, filename=os.path.join('{} Shows World.html'.format(artist)),
                              auto_open=False, show_link=False, config={'displayModeBar': False, 'scrollZoom': True,
                                                                        'showAxisDragHandles': True})
    plot_world_code = get_plot(plot_world)
    return plot_county_code, plot_state_code, plot_world_code