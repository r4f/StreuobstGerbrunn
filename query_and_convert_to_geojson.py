import json
import os
import re
import sys
import time
from dataclasses import dataclass
from enum import Enum
from operator import itemgetter

import requests
from osmtogeojson import osmtogeojson

BBOX_SOUTH = os.environ["BBOX_SOUTH"]
BBOX_WEST = os.environ["BBOX_WEST"]
BBOX_NORTH = os.environ["BBOX_NORTH"]
BBOX_EAST = os.environ["BBOX_EAST"]

# Tried in order. Overpass servers are often busy, so we retry and fall back.
overpass_urls = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
# Overpass rejects the default "python-requests" User-Agent with 406.
headers = {"User-Agent": "Naschbaumkarte (https://github.com/r4f/StreuobstGerbrunn)"}
local_trees_file = "data/trees.json"
geojson_result_file = "deploy/trees.geojson"

query_content = f"""
    [out:json][timeout:25];
    node({BBOX_SOUTH},{BBOX_WEST},{BBOX_NORTH},{BBOX_EAST})[natural=tree]
    ;
    out;
"""


class Image(Enum):
    Apple = "apple"
    Pear = "pear"
    Chestnut = "chestnut"
    Quince = "quince"
    Plum = "plum"
    Fig = "fig"
    Fallback_ = "Circled_dot"
    Peach = "peach"
    Walnut = "walnut"
    Cherry = "cherry"
    Mulberry = "mulberry"
    Speierling = "speierling"
    NoImage = None


class Tag(Enum):
    Genus = "genus"
    Species = "species"
    GenusDE = "genus:de"
    SpeciesDE = "species:de"


@dataclass
class Fruit:
    display_name: str
    image: Image
    conditions: list[dict]
    # Used by the search on the map to combine related fruits, e.g. all cherries.
    # Defaults to display_name.
    group: str | None = None

    def one_condition_holds(self, tags):
        for condition in self.conditions:
            if all(condition[k] == tags.get(k.value) for k in condition):
                return True
        return False


fruits = [
    Fruit(
        display_name="Apfel",
        image=Image.Apple,
        conditions=[
            {Tag.Genus: "Malus"},
            {Tag.GenusDE: "Apfel"},
            {Tag.Species: "Malus domestica"},
            {Tag.SpeciesDE: "Apfel"},
        ],
    ),
    Fruit(
        display_name="Birne",
        image=Image.Pear,
        conditions=[
            {Tag.Genus: "Pyrus"},
            {Tag.GenusDE: "Birne"},
            {Tag.Species: "Pyrus communis"},
            {Tag.SpeciesDE: "Birne"},
        ],
    ),
    Fruit(
        display_name="Quitte",
        image=Image.Quince,
        conditions=[
            {Tag.Genus: "Cydonia"},
            {Tag.Species: "Cydonia oblonga"},
            {Tag.Species: "Cydonia vulgaris"},
        ],
    ),
    Fruit(
        display_name="Zwetschge",
        group="Pflaume/Zwetschge",
        image=Image.Plum,
        conditions=[{Tag.Species: "Prunus domestica subsp. domestica"}],
    ),
    Fruit(
        display_name="Pflaume",
        group="Pflaume/Zwetschge",
        image=Image.Plum,
        conditions=[{Tag.Species: "Prunus domestica"}],
    ),
    Fruit(
        display_name="Kirschpflaume",
        group="Pflaume/Zwetschge",
        image=Image.Fallback_,
        conditions=[
            {Tag.Species: "Prunus cerasifera"},
        ],
    ),
    Fruit(
        display_name="Süßkirsche",
        group="Kirsche",
        image=Image.Cherry,
        conditions=[
            {Tag.Species: "Prunus avium"},
            {Tag.SpeciesDE: "Süßkirsche"},
        ],
    ),
    Fruit(
        display_name="Sauerkirsche",
        group="Kirsche",
        image=Image.Cherry,
        conditions=[
            {Tag.Species: "Prunus cerasus"},
            {Tag.SpeciesDE: "Sauerkirsche"},
        ],
    ),
    Fruit(
        display_name="Kirsche",
        image=Image.Cherry,
        conditions=[
            {Tag.GenusDE: "Kirsche"},
            {Tag.Genus: "Prunus subg. Cerasus"},
        ],
    ),
    Fruit(
        display_name="Weiße Maulbeere",
        group="Maulbeere",
        image=Image.Mulberry,
        conditions=[
            {Tag.Species: "Morus alba"},
            {Tag.SpeciesDE: "Weiße Maulbeere"},
        ],
    ),
    Fruit(
        display_name="Schwarze Maulbeere",
        group="Maulbeere",
        image=Image.Mulberry,
        conditions=[
            {Tag.Species: "Morus nigra"},
            {Tag.SpeciesDE: "Schwarze Maulbeere"},
        ],
    ),
    Fruit(
        display_name="Rote Maulbeere",
        group="Maulbeere",
        image=Image.Mulberry,
        conditions=[
            {Tag.Species: "Morus rubra"},
            {Tag.SpeciesDE: "Rote Maulbeere"},
        ],
    ),
    Fruit(
        display_name="Maulbeere",
        image=Image.Mulberry,
        conditions=[
            {Tag.Genus: "Morus"},
        ],
    ),
    Fruit(
        display_name="Feige",
        image=Image.Fig,
        conditions=[],
    ),
    Fruit(
        display_name="Pfirsisch",
        image=Image.Peach,
        conditions=[],
    ),
    Fruit(
        display_name="Walnuss",
        image=Image.Walnut,
        conditions=[{Tag.Genus: "Juglans"}],
    ),
    Fruit(
        display_name="Eiche",
        image=Image.NoImage,
        conditions=[
            {Tag.Genus: "Quercus"},
        ],
    ),
    Fruit(
        display_name="Birke",
        image=Image.NoImage,
        conditions=[
            {Tag.Genus: "Betula"},
        ],
    ),
    Fruit(
        display_name="Kastanie",
        image=Image.Chestnut,
        conditions=[
            {Tag.Genus: "Castanea"},
        ],
    ),
    Fruit(
        display_name="Rosskastanie",
        image=Image.NoImage,
        conditions=[
            {Tag.Genus: "Aesculus"},
        ],
    ),
    Fruit(
        display_name="Linde",
        image=Image.NoImage,
        conditions=[
            {Tag.Genus: "Tilia"},
        ],
    ),
    Fruit(
        display_name="Mehlbeere",
        image=Image.Fallback_,
        conditions=[
            {Tag.Genus: "Sorbus"},
            {Tag.Genus: "Scandosorbus"},
        ],
    ),
    Fruit(
        display_name="Schwarzer Holunder",
        group="Holunder",
        image=Image.Fallback_,
        conditions=[
            {Tag.Species: "Sambucus nigra"},
            {Tag.SpeciesDE: "Schwarzer Holunder"},
        ],
    ),
    Fruit(
        display_name="Holunder",
        image=Image.Fallback_,
        conditions=[
            {Tag.Genus: "Sambucus"},
        ],
    ),
    Fruit(
        display_name="Speierling",
        image=Image.Speierling,
        conditions=[
            # {Tag.Genus: "Cormus"},
            {Tag.Species: "Cormus domestica"},
        ],
    ),
    Fruit(
        display_name="",
        image=Image.Fallback_,
        conditions=[{}],
    ),
]


def query_overpass(query: str, attempts_per_server: int = 3) -> dict:
    """Run the query, retrying on busy servers. Raises RuntimeError on failure."""
    errors = []
    for url in overpass_urls:
        for attempt in range(attempts_per_server):
            try:
                response = requests.post(
                    url, data={"data": query}, headers=headers, timeout=60
                )
            except requests.RequestException as e:
                errors.append(f"{url}: {e}")
                time.sleep(2**attempt)
                continue
            if response.status_code == 200:
                try:
                    result = response.json()
                except ValueError:
                    errors.append(f"{url}: response is not JSON")
                    break
                # Overpass reports query errors (e.g. timeouts) inside a 200 response.
                if "remark" in result and not result.get("elements"):
                    errors.append(f"{url}: {result['remark']}")
                    break
                return result
            errors.append(f"{url}: HTTP {response.status_code}")
            # 429 = rate limited, 5xx = busy. Anything else will not get better.
            if response.status_code != 429 and response.status_code < 500:
                break
            time.sleep(2**attempt * 3)
    raise RuntimeError("Overpass query failed:\n  " + "\n  ".join(errors))


if os.environ.get("USE_LOCAL_TREES_FILE", "false") == "true":
    with open(local_trees_file) as f:
        response_dict = json.load(f)
else:
    try:
        response_dict = query_overpass(query_content)
    except RuntimeError as e:
        if not os.path.exists(local_trees_file):
            sys.exit(str(e))
        print(e, f"\nFalling back to cached {local_trees_file}.", file=sys.stderr)
        with open(local_trees_file) as f:
            response_dict = json.load(f)
    else:
        with open(local_trees_file, "w") as f:
            json.dump(response_dict, f, indent=2)

pattern = re.compile(r"(\d+\.?\d*)\s*(m|cm|mm)", re.IGNORECASE)


def normalize_length(length_value: str):
    try:
        f = float(length_value)
        return f
    except Exception:
        match = pattern.match(length_value)
        if match:
            # Extract the numeric value (Group 1) and the unit (Group 2)
            value_str, unit = match.groups()
            value = float(value_str)
            match unit:
                case "m":
                    return value
                case "cm":
                    return value / 100
                case "mm":
                    return value / 1000
        else:
            print("Could not match", length_value)
            return 0.5


for feature in response_dict["elements"]:
    tags = feature["tags"]

    # try to find the correct fruit based on the tags.
    fruit = None
    for f in fruits:
        if f.one_condition_holds(tags):
            fruit = f
            break

    if fruit is not None:
        tags["_display_name"] = fruit.display_name
        if fruit.display_name:
            tags["_group"] = fruit.group or fruit.display_name
        if fruit.image.value is not None:
            tags["_image"] = fruit.image.value
    if "circumference" in tags:
        tags["circumference"] = normalize_length(tags["circumference"])

# sort response elements by latitude
response_dict["elements"] = sorted(response_dict["elements"], key=itemgetter("lat"))


geojson_data = osmtogeojson.process_osm_json(response_dict)

with open(geojson_result_file, "w") as f:
    json.dump(geojson_data, f, indent=2)
