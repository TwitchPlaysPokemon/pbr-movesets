import json
import os

import pokecat
import yaml
from yaml.cyaml import CLoader

with open(os.path.expandvars("${HOME}/files.json")) as f:
    changed_files = json.load(f)

for changed_file in changed_files:
    if not changed_file.startswith("pokesets/") or os.path.splitext(changed_file)[1].lower() not in (".yml", ".yaml"):
        print("{} is not a pokeset".format(changed_file))
        continue
    print("{} is a pokeset".format(changed_file))
    with open(changed_file) as f:
        num_lines = sum(1 for line in f)
    with open(changed_file) as f:
        raw_sets = list(yaml.load_all(f, Loader=CLoader))
    info_text = "Stats (Not a warning, just for information):\n"
    for raw_set in raw_sets:
        pokeset = pokecat.instantiate_pokeset(pokecat.populate_pokeset(raw_set, skip_ev_check=True))
        stats = pokeset["stats"]
        info_text += "{} {}: {} hp, {} atk, {} def, {} spe, {} spA, {} spD\n".format(
            pokeset["species"]["name"], pokeset["setname"],
            stats["hp"], stats["atk"], stats["def"], stats["spe"], stats["spA"], stats["spD"])
    print("::warning file={},line={}::{}".format(changed_file, num_lines, info_text.replace("\n", "%0A")))
