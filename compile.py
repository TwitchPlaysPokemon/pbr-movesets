
import os
import sys
import logging
import warnings
import json
from collections import defaultdict, Counter
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
outfile = "pbrpokemondb.json"

existing_ids = {}
genders_per_species = defaultdict(set)

illegal_chars = r"[\]^`|"

for dir, _, files in os.walk("."):
    for file in files:
        if not (file.endswith(".yaml") or file.endswith(".yml")) or file == outfile or file.startswith("_"):
            continue
        filepath = os.path.join(dir, file)
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                contents = list(yaml.load_all(f))
                for pokeset in contents:
                    if not pokeset:
                        print("Skipping empty pokeset in {}".format(filepath))
                        continue
                    identifier = "{}:{} {}".format(filepath, pokeset.get("species"), pokeset.get("setname"))
                    with warnings.catch_warnings(record=True) as w:
                        if "ingamename" in pokeset:
                            fixed_ingamename = pokeset["ingamename"].encode("ascii", "replace").decode()
                            for char in illegal_chars:
                                fixed_ingamename = fixed_ingamename.replace(char, "?")
                            if pokeset["ingamename"] != fixed_ingamename:
                                print("CHANGED INGAMENAME TO {} AS A TEMPORARY FIX TO AVOID ENCODING ISSUES"
                                      .format(fixed_ingamename))
                                pokeset["ingamename"] = fixed_ingamename
                        try:
                            pokeset = pokecat.populate_pokeset(pokeset, skip_ev_check=True)
                        except ValueError as ex:
                            print("{}> ERROR: {}".format(identifier, str(ex).encode("ascii", "replace").decode()))
                        else:
                            for warning in w:
                                print("{}> WARNING: {}".format(identifier, str(warning.message).encode("ascii", "replace").decode()))
                            genders_this_species = genders_per_species[pokeset["species"]["id"]]
                            genders_this_species |= set(pokeset["gender"])
                            if None in genders_this_species and len(genders_this_species) > 1:
                                print("{}> ERROR: Starting with this set, that species now has both genderless and genderful sets! "
                                      "Stick to either genderless or genderful per species or PBR might crash!"
                                      .format(identifier))
                            id = (pokeset["species"]["id"], pokeset["setname"])
                            if id in existing_ids:
                                prev_identifier = existing_ids[id]
                                print("{}> ERROR: combination of species {} ({}) and setname {} already exists ({}), but must be unique!"
                                      .format(identifier, id[0], pokeset["species"]["name"], id[1], prev_identifier))
                            else:
                                existing_ids[id] = identifier
                                sets += [pokeset]
            except yaml.YAMLError as e:
                print("Error reading file: {}/{}: {}".format(dir, file, str(e).encode("ascii", "replace").decode()))
            except:
                print("Error reading file: {}/{}".format(dir, file))
                raise

print("Writing compiled sets to {}...".format(outfile))
with open(outfile, "w+", encoding="utf-8") as f:
    json.dump(sets, f, indent="    ", sort_keys=True)


group_tags_file = "group_tags.json"
group_tags = {}
runmons = Counter()
anime = Counter()
pwt = Counter()
for set in sets:
    tags = set['tags']
    if 'runmon' in tags:
        runmons["setname+" + set['setname']] += 1
    if 'anime' in tags:
        anime["setname+" + set['setname']] += 1
    if 'in-game' in tags:
        pwt_set = next(filter(lambda tag: 'PWT' in tag, tags))
        pwt[pwt_set] += 1

group_tags['runmons'] = [elem for (elem, cnt) in runmons.items() if cnt >= 3]
group_tags['anime'] = [elem for (elem, cnt) in anime.items() if cnt >= 3]
group_tags['pwt'] = [elem for (elem, cnt) in pwt.items() if cnt >= 3]
group_tags['runmons_less_than_3_mons'] = [elem for (elem, cnt) in runmons.items() if cnt < 3]
group_tags['anime_less_than_3_mons'] = [elem for (elem, cnt) in anime.items() if cnt < 3]
group_tags['pwt_less_than_3_mons'] = [elem for (elem, cnt) in pwt.items() if cnt < 3]

print("Writing group tag data to {}...".format(group_tags_file))
with open(group_tags_file, "w+", encoding="utf-8") as f:
    json.dump(group_tags, f, sort_keys=True)
