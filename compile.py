
import os
import sys
import logging
import warnings
import json
try:
    import yaml
except ImportError:
    print("Your python installation must have pyyaml installed.")
    sys.exit()
try:
    import pokecat
except ImportError:
    print("Your python installation must have pokecat installed.")
    sys.exit()


sets = []
outfile = "_compiled.json"

existing_ids = {}

for dir, _, files in os.walk("."):
    for file in files:
        if not file.endswith(".yaml") or file == outfile or file.startswith("_"):
            continue
        filepath = os.path.join(dir, file)
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                contents = list(yaml.load_all(f))
                for set in contents:
                    if not set:
                        print("Skipping empty set in {}".format(filepath))
                        continue
                    identifier = "{}:{} {}".format(filepath, set.get("species"), set.get("setname"))
                    with warnings.catch_warnings(record=True) as w:#
                        try:
                            set = pokecat.populate_pokeset(set)
                        except ValueError as ex:
                            print("{}> ERROR: {}".format(identifier, ex))
                        else:
                            for warning in w:
                                print("{}> WARNING: {}".format(identifier, warning.message))
                            id = (set["species"]["id"], set["setname"])
                            if id in existing_ids:
                                prev_identifier = existing_ids[id]
                                print("{}> ERROR: combination of species {} ({}) and setname {} already exists ({}), but must be unique!"
                                      .format(identifier, id[0], set["species"]["name"], id[1], prev_identifier))
                            else:
                                existing_ids[id] = identifier
                                sets += [set]
            except yaml.YAMLError as e:
                print("Error reading file: {}/{}: {}".format(dir, file, e))

print("Writing output to {}...".format(outfile))
with open(outfile, "w+", encoding="utf-8") as f:
    json.dump(sets, f, indent="    ")
