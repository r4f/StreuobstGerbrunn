import os
import shutil

from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = "templates"

BBOX_SOUTH = float(os.environ["BBOX_SOUTH"])
BBOX_WEST = float(os.environ["BBOX_WEST"])
BBOX_NORTH = float(os.environ["BBOX_NORTH"])
BBOX_EAST = float(os.environ["BBOX_EAST"])
CENTER_LON = float(os.environ.get("CENTER_LON") or 0.5 * (BBOX_WEST + BBOX_EAST))
CENTER_LAT = float(os.environ.get("CENTER_LAT") or 0.5 * (BBOX_SOUTH + BBOX_NORTH))
INITIAL_ZOOM = float(os.environ.get("INITIAL_ZOOM", 15))

display_condition = os.environ.get("DISPLAY_CONDITION")
if display_condition is not None:
    key, value = display_condition.split("==")
    display_conditions = f'["==", "{key}", "{value}"],'
else:
    display_conditions = ""

loader = FileSystemLoader(TEMPLATE_DIR)
env = Environment(loader=loader)

display_areas = os.environ.get("DISPLAY_AREAS", "false") == "true"
if display_areas:
    areas_geojson_file = os.environ.get("AREAS_GEOJSON_FILE")
    if areas_geojson_file is None:
        raise ValueError(
            "To display areas, a geojson file must be provided and set in .env."
        )
    shutil.copy2(areas_geojson_file, "deploy/areas.geojson")


with open("deploy/index.html", "w") as f:
    template = env.get_template("index.html")
    output = template.render({"WEBSITE_TITLE": os.environ.get("WEBSITE_TITLE", "")})
    f.write(output)

context = dict(
    BBOX_SOUTH=BBOX_SOUTH,
    BBOX_WEST=BBOX_WEST,
    BBOX_NORTH=BBOX_NORTH,
    BBOX_EAST=BBOX_EAST,
    INITIAL_ZOOM=INITIAL_ZOOM,
    center_lon=CENTER_LON,
    center_lat=CENTER_LAT,
    display_areas=display_areas,
    display_conditions=display_conditions,
)

with open("deploy/main.js", "w") as f:
    template = env.get_template("main.js")
    output = template.render(context)
    f.write(output)
