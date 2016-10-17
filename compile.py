
import os
import sys
import logging
import warnings
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
outfile = "compiled.yaml"

for dir, _, files in os.walk("."):
    for file in files:
        if not file.endswith(".yaml") or file == outfile:
            continue
        filepath = os.path.join(dir, file)
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                contents = list(yaml.load_all(f))
                for set in contents:
                    identifier = "{}:{} {}".format(filepath, set.get("species"), set.get("setname"))
                    with warnings.catch_warnings(record=True) as w:#
                        try:
                            sets += [pokecat.populate_pokeset(set)]
                            for warning in w:
                                print("{}> WARNING: {}".format(identifier, warning.message))
                        except ValueError as ex:
                            print("{}> ERROR: {}".format(identifier, ex))
            except yaml.YAMLError as e:
                print("Error reading file: {}/{}: {}".format(dir, file, e))

print("Writing output to {}...".format(outfile))
with open(outfile, "w+", encoding="utf-8") as f:
    yaml.dump_all(sets, f)
