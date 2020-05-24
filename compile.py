
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

illegal_chars = r"[\]^`|<>_{}"

name_replacements = {"ᴹ": "M", "ɴ": "N", "×": "x", "’": "'", "”": "\"", "ᵖ": "P", "ᵏ": "K", " ": " ", "ᴾ": "P"}

allowed_characters = ["\u2640", "\u2642", "â", "É"]

for dir, _, files in os.walk("."):
    for file in files:
        if not (file.endswith(".yaml") or file.endswith(".yml")) or file == outfile or file.startswith("_"):
            continue
        filepath = os.path.join(dir, file)
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                contents = list(yaml.load_all(f, Loader=yaml.FullLoader))
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
                            temp = ""
                            for i, char in enumerate(pokeset["ingamename"]):
                                if char in allowed_characters:
                                    temp += char
                                elif char in name_replacements:
                                    temp += name_replacements[char]
                                else:
                                    temp += fixed_ingamename[i]
                            fixed_ingamename = temp
                            if pokeset["ingamename"] != fixed_ingamename:
                                print("Changed ingamename: {} -> {} to avoid encoding issues"
                                      .format(pokeset["ingamename"], fixed_ingamename))
                                pokeset["ingamename"] = fixed_ingamename
                        try:
                            pokeset = pokecat.populate_pokeset(pokeset, skip_ev_check=True)
                        except ValueError as ex:
                            print("{}> ERROR: {}".format(identifier, str(ex).encode("ascii", "replace").decode()))
                        else:
                            for warning in w:
                                text = str(warning.message).encode("ascii", "replace").decode()
                                if text != "Set is shiny, but not hidden, which means it is publicly visible. Is this intended?" and text != "Set is shiny, but also biddable, which means it can be used in token matches. Is this intended?" and not text.startswith("Sum of EV must not be larger than") and "is guaranteed to occupy multiple slots (possible stallmate due to PP-bug)" not in text:
                                    print("{}> WARNING: {}".format(identifier, text))
                            genders_this_species = genders_per_species[pokeset["species"]["id"]]
                            genders_this_species |= set(pokeset["gender"])
                            if None in genders_this_species and len(genders_this_species) > 1:
                                print("{}> ERROR: Starting with this set, that species now has both genderless and genderful sets! "
                                      "Stick to either genderless or genderful per species or PBR might crash!"
                                      .format(identifier))
                                continue  # Crash risk, so do NOT add this pokeset
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
        trainer_tag ="setname+" + set['setname']
        runmons[trainer_tag] += 1
    if 'anime' in tags:
        trainer_tag = "setname+" + set['setname']
        anime[trainer_tag] += 1
    if 'in-game' in tags:
        trainer_tag = list(filter(lambda tag: 'PWT' in tag, tags))
        if trainer_tag:
            pwt_set = trainer_tag[0]
            pwt[pwt_set] += 1

group_tags['pwt_versus_tags'] = [elem for (elem, cnt) in pwt.items() if cnt >= 4]
group_tags['pwt_versus_tags'] += [elem for (elem, cnt) in runmons.items() if cnt >= 4]

print("Writing group tag data to {}...".format(group_tags_file))
with open(group_tags_file, "w+", encoding="utf-8") as f:
    json.dump(group_tags, f, sort_keys=True, ensure_ascii=False)
