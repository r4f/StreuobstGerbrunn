from dataclasses import dataclass
import requests
import json
from osmtogeojson import osmtogeojson
from enum import Enum, auto

overpass_url="https://overpass-api.de/api/interpreter"
geojson_result_file="deploy/trees.geojson"

query_content = """
    [out:json][timeout:25];
    node(49.768,9.972,49.794,10.04)[natural=tree];
    out;
"""

class Image(Enum):
    Apple = "apple"
    Pear = "pear"
    Quince = "quince"
    Plum = "plum"
    Fig = "fig"
    Fallback_ = "Circled_dot"
    Peach = "peach"
    Walnut = "walnut"
    Cherry = "cherry"

class Tag(Enum):
    Genus = "genus"
    Species = "species"
    GenusDE = "genus:de"
    SpeciesDE = "species:de"

@dataclass
class Fruit():
    display_name: str
    image: Image
    conditions: list[dict]

    def one_condition_holds(self, tags):
        for condition in self.conditions:
            if all(condition[k]==tags.get(k.value) for k in condition.keys()):
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
        image=Image.Plum,
        conditions=[
            {Tag.Species: "Prunus domestica subsp. domestica"}
        ],
    ),
    Fruit(
        display_name="Pflaume",
        image=Image.Plum,
        conditions=[
            {Tag.Species: "Prunus domestica"}
        ],
    ),
    Fruit(
        display_name="Kirschpflaume",
        image=Image.Fallback_,
        conditions=[
            {Tag.Species: "Prunus cerasifera"},
        ],
    ),
    Fruit(
        display_name="Süßkirsche",
        image=Image.Cherry,
        conditions=[
            {Tag.Species: "Prunus avium"},
            {Tag.SpeciesDE: "Süßkirsche"},
        ],
    ),
    Fruit(
        display_name="Sauerkirsche",
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
        image=Image.Fallback_,
        conditions=[
            {Tag.Species: "Morus alba"},
            {Tag.SpeciesDE: "Weiße Maulbeere"},
        ]
    ),
    Fruit(
        display_name="Schwarze Maulbeere",
        image=Image.Fallback_,
        conditions=[
            {Tag.Species: "Morus nigra"},
            {Tag.SpeciesDE: "Schwarze Maulbeere"},
        ]
    ),
    Fruit(
        display_name="Rote Maulbeere",
        image=Image.Fallback_,
        conditions=[
            {Tag.Species: "Morus rubra"},
            {Tag.SpeciesDE: "Rote Maulbeere"},
        ]
    ),
    Fruit(
        display_name="Feige",
        image=Image.Fig,
        conditions=[
        ],
    ),
    Fruit(
        display_name="Pfirsisch",
        image=Image.Peach,
        conditions=[
        ],
    ),
    Fruit(
        display_name="Walnuss",
        image=Image.Walnut,
        conditions=[
            {Tag.Genus: "Juglans"}
        ],
    ),
    Fruit(
        display_name="Eiche",
        image=Image.Fallback_,
        conditions=[
            {Tag.Genus: "Quercus"},
        ],
    ),
    Fruit(
        display_name="Birke",
        image=Image.Fallback_,
        conditions=[
            {Tag.Genus: "Betula"},
        ],
    ),
    Fruit(
        display_name="Kastanie",
        image=Image.Fallback_,
        conditions=[
            {Tag.Genus: "Castanea"},
        ],
    ),
    Fruit(
        display_name="Rosskastanie",
        image=Image.Fallback_,
        conditions=[
            {Tag.Genus: "Aesculus"},
        ],
    ),
    Fruit(
        display_name="Linde",
        image=Image.Fallback_,
        conditions=[
            {Tag.Genus: "Tilia"},
        ],
    ),
    Fruit(
        display_name="Mehlbeere",
        image=Image.Fallback_,
        conditions=[
            {Tag.Genus: "Sorbus"},
        ],
    ),
]

@dataclass
class Genus:
    genus: str
    genus_de: str
    image: Image
    display_name: str
    wikidata: str

@dataclass
class Species:
    genus: Genus
    species: str
    species_de: str
    image: Image
    display_name: str
    wikidata: str

@dataclass
class Taxon:
    species: Species
    taxon_cultivar: str
    #taxon_cultivar_de: str
    image: Image
    display_name: str
    wikidata: str


#Genus(
#    genus="Surbus",
#    genus_de="Mehlbeere",
#    wikidata="Q157964",
#)
#
#Genus(
#    genus="Malus",
#    genus_de="Apfel",
#    wikidata="Q104819",
#)
#
#
#
#
#
#Species(
#    species="Malus domestica",
#    species_de="Kulturapfel",
#    wikidata="Q18674606",
#)
#
#schoener_aus_boskoop = Taxon(
#    taxon_cultivar="Schöner aus Boskoop",
#    wikidata="Q504565",
#)
#
#taxon_normalizations = {
#    "Roter Boskoop": schoener_aus_boskoop,
#}
#
#def get_Sorte(tags: dict) -> Sorte | None:
#    for sorte, conditions in sorten_map.items():
#        for c in conditions:
#            if all(tags.get(k.value)==v for k, v in c.items()):
#                return sorte
#    return None

with requests.post(url=overpass_url, data=query_content) as response:
    response_dict = json.loads(response.text)

with open("trees.json", "w") as f:
    json.dump(response_dict, f, indent=2)

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
        tags["_image"] = fruit.image.value
    if "circumference" in tags:
        tags["circumference"] = float(tags["circumference"])

geojson_data = osmtogeojson.process_osm_json(response_dict)

with open(geojson_result_file, "w") as f:
    json.dump(geojson_data, f, indent=2)
