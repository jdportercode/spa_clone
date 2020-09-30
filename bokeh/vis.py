import math
import os
import re
import time
import json
import sys
import signal
from pathlib import Path
from collections import defaultdict, Counter

# from shapely.geometry import Point, Polygon
import pandas
import geopandas as gpd
import shapely
# from bokeh.io import show, output_file
from bokeh.models import (
    LinearColorMapper,
    Circle,
    MultiPolygons,
    GeoJSONDataSource,
    HoverTool,
    WheelZoomTool,
    PanTool,
    Panel,
    Tabs,
    WMTSTileSource,
    CustomJS,
    Div,
    # MultiSelect,
    MultiChoice,
    # ColumnDataSource,
    # TapTool,
    # OpenURL,
    # CustomJSHover,
)
from bokeh.layouts import column, row
from bokeh.palettes import Blues8 as palette
from bokeh.plotting import figure
from bokeh.resources import JSResources
from bokeh.embed import (
    # file_html,
    components,
)

def base_map(tile_url, tile_attribution='MapTiler'):
    # Plot
    p = figure(
        title="",
        plot_width=600, plot_height=700,
        x_axis_location=None, y_axis_location=None,
        y_range=(-4300000, 4600000),
        x_range=(-2450000, 6450000),
        x_axis_type="mercator", y_axis_type="mercator",
        )

    zoom = WheelZoomTool()
    p.add_tools(zoom)
    p.toolbar.active_scroll = zoom

    drag = PanTool()
    p.add_tools(drag)
    p.toolbar.active_drag = drag

    p.toolbar_location = None
    p.grid.grid_line_color = None

    p.add_tile(WMTSTileSource(
        url=tile_url,
        attribution=tile_attribution
    ))

    return p

def points(plot, div, point_source):
    point = Circle(x='x', y='y', fill_color="purple", fill_alpha=0.5,
                   line_color="gray", line_alpha=0.5, size=6, name="points")
    cr = plot.add_glyph(point_source,
                        point,
                        hover_glyph=point,
                        selection_glyph=point,
                        name="points")
    callback = CustomJS(args=dict(source=point_source, div=div),
                        code="""
        var features = source['data'];
        var indices = cb_data.index.indices;

        if (indices.length != 0) {
            div.text = "Number of protests: " + indices.length + "<br>"
            var counter = 0;
            for (var i = 0; i < indices.length; i++) {
                if (counter == 5) {
                    if (indices.length == 6) {
                        div.text = div.text + "<br>" + "<em>" +
                                   "Additional protest not shown" +
                                   "</em>" +  "<br>";
                    } else {
                        div.text = div.text + "<br>" + "<em>" +
                                   "Additional " + (indices.length -5) +
                                   " protests not shown" + "</em>" +  "<br>";
                    }
                    break;
                } else {
                    counter++;
                }
                var protest = indices[i];
                var desc = features['Description of Protest'][protest];
                var uni = features['School Name'][protest];
                var type = features['Event Type (F3)'][protest];
                div.text = div.text + counter + '.' + '<br>' +
                           'Description: ' + desc + '<br>' + ' Location: ' +
                           uni + '<br>' + ' Type of Protest: ' + type +
                           '<br>';
                }
        }
    """)
    hover = HoverTool(
        tooltips=None,
        point_policy="follow_mouse",
        renderers=[cr],
        callback=callback
    )
    plot.add_tools(hover)
    plot.toolbar.active_inspect = hover

class Map:
    def __init__(self):
        self.protests = load_protests()
        self.nations = load_geojson()
        self.filters = self.collect_filters()
        sum_protests(self.protests, self.nations)

    def point_plot(self, title, tile_url, tile_attribution='MapTiler'):
        plot = base_map(tile_url, tile_attribution)

        div = Div(width=plot.plot_width // 2,
                  height=plot.plot_height,
                  height_policy="fixed")

        point_source = GeoJSONDataSource(geojson=self.protests.to_json())
        points(plot, div, point_source)
        select_col = [one_filter(plot, point_source, filter_name)
                      for filter_name in self.filters]
        select_col = column(*select_col)
        map_select = row(plot, select_col)
        layout = column(map_select, div)
        return Panel(child=layout, title=title)

def save_embed(plot):
    with open("jekyll/_includes/vis/vis.html", 'w', encoding='utf-8') as op:
        save_components(plot, op)

    # This ensures that the right version of BokehJS is always in use
    # on the jekyll site.
    with open('jekyll/_includes/bokeh_heading.html',
              'w', encoding='utf-8') as op:
        save_script_tags(op)

def save_html(plot):
    with open("map-standalone.html", 'w', encoding='utf-8') as op:
        op.write("""
        <!DOCTYPE html>
        <html lang="en">
        """)

        save_script_tags(op)
        save_components(plot, op)

        op.write("""
        <div id="map-hover-context">
        </div>
        </html>
        """)


def save_script_tags(open_file):
    # This loads more JS files than is strictly necessary. We really only
    # need the main bokeh file and the widgets file. But it's not yet clear
    # that the gain in loading time is worth the extra complexity of weeding
    # out the other files.
    for f in JSResources(mode='cdn').js_files:
        open_file.write(
            f'<script type="text/javascript" src="{f}" '
            'crossorigin="anonymous"></script>\n'
        )

    open_file.write(
        '<script type="text/javascript"> \n'
        '    Bokeh.set_log_level("info"); \n'
        '</script>\n'
    )


def save_components(plot, open_file):
    for c in components(plot):
        open_file.write(c)
        open_file.write('\n')

# May need to move away from maptiler at some point (e.g. to a free thing)
def main(embed=True):
    point_key = ('https://api.maptiler.com/maps/streets/{z}/{x}/{y}.png?'
                 'key=xEyWbUmfIFzRcu729a2M')

    map = Map()
    vis = map.point_plot("Protest", point_key)
    if embed:
        save_embed(vis)
    else:
        save_html(vis)


if __name__ == "__main__":

    if '--standalone' in sys.argv[1:]:
        print("Generating standalone map...")
        main(embed=False)
    else:
        # Get the default signal handler for SIGTERM (see below)
        default_sigterm = signal.getsignal(signal.SIGTERM)

        # We set these variables to keep track of changes
        temp_time = 0
        recent_time = 0
        print("Watching input directory for changes every ten seconds.")
        while True:
            for data_file in os.listdir("data_to_map/data"):
                mod_time = os.path.getmtime(os.path.join("data_to_map/data",
                                                         data_file))
                if mod_time > recent_time:
                    recent_time = mod_time
            if recent_time > temp_time:
                temp_time = recent_time
                print("Change detected, generating new map...")
                main()
                print("Map generation complete.")
                print("Watching for changes...")

            # Listen for SIGTERM from docker while sleeping.
            signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))
            time.sleep(10)
            # Ignore SIGTERM while working.
            signal.signal(signal.SIGTERM, default_sigterm)

