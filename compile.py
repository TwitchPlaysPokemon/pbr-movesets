"""
Module for parsing and analyzing all pokeset files within a repository directory.
"""
import logging
import os
import warnings
from enum import Enum
from itertools import groupby, chain
from typing import Optional

import pokecat
import yaml
import yaml.scanner

logger = logging.getLogger(__name__)

ILLEGAL_CHARS = r"[\]^`|<>_{}"
NAME_REPLACEMENTS = {"ᴹ": "M", "ɴ": "N", "×": "x", "’": "'", "”": "\"", "ᵖ": "P", "ᵏ": "K", " ": " ", "ᴾ": "P"}
ALLOWED_CHARACTERS = ["\u2640", "\u2642", "â", "É"]


class Severity(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    NOTE = "NOTE"


class Note:
    def __init__(self, severity: Severity, message, pokeset_identifier=None, filepath=None, position=None):
        self.severity = severity
        self.message = message
        self.pokeset_identifier = pokeset_identifier
        self.filepath = filepath
        self.position = position  # line offset in file, if known

    @property
    def ident(self):
        return "{}, {}".format(*self.pokeset_identifier) if self.pokeset_identifier else "unknown pokeset"

    def __str__(self):
        if self.filepath:
            return "[{}] [{} @ {}]: {}".format(self.severity.name, self.ident, self.filepath, self.message)
        else:
            return "[{}] [{}]: {}".format(self.severity.name, self.ident, self.message)

    def __repr__(self):
        return ("Note({!r}, {!r}, {!r}, {!r}, {!r})"
                .format(self.severity, self.message, self.pokeset_identifier, self.filepath, self.position))


def find_prototype_file(base_dir, rel_path) -> Optional[bytes]:
    while rel_path:
        for filename in os.listdir(os.path.join(base_dir, rel_path)):
            if filename.lower() in ("_prototype.yaml", "_prototype.yml"):
                return os.path.join(base_dir, rel_path, filename)
        rel_path = os.path.dirname(rel_path)
    return None


def analyze_dir(root_dir):
    pokesets = []
    notes = []
    for dirname, _, filenames in os.walk(root_dir):
        prototype_filepath = find_prototype_file(root_dir, os.path.relpath(dirname, start=root_dir))
        prototype = None
        if prototype_filepath:
            with open(prototype_filepath, encoding="utf-8") as file_obj:
                try:
                    prototype = yaml.load(file_obj, Loader=yaml.CLoader)
                except yaml.MarkedYAMLError as e:
                    notes.append(Note(
                        Severity.ERROR,
                        "Invalid prototype file: " + str(e),
                        position=e.problem_mark.line,
                    ))
                except yaml.YAMLError as e:
                    notes.append(Note(
                        Severity.ERROR,
                        "Invalid prototype file: " + str(e),
                    ))
        for filename in filenames:
            filepath = os.path.join(dirname, filename)
            relpath = os.path.relpath(filepath, root_dir)
            if not filename.endswith((".yaml", ".yml")) or filename.startswith("_"):
                continue
            with open(filepath, encoding="utf-8") as file_obj:
                its_notes, its_pokesets = analyze_file(file_obj, prototype=prototype)
                for note in its_notes:
                    note.filepath = relpath
                notes += its_notes
                pokesets += its_pokesets
    its_notes, pokesets = analyze_all_pokesets_integrity(pokesets)
    notes += its_notes
    return notes, pokesets


def analyze_file(file_obj, prototype=None):
    pokesets = []
    notes = []
    try:
        raw_pokesets = list(yaml.load_all(file_obj, Loader=yaml.CLoader))
    except yaml.MarkedYAMLError as e:
        notes.append(Note(
            Severity.ERROR,
            str(e),
            position=e.problem_mark.line,
        ))
    except yaml.YAMLError as e:
        notes.append(Note(
            Severity.ERROR,
            str(e),
        ))
    else:
        for raw_pokeset in raw_pokesets:
            if not raw_pokeset:
                logger.info("Skipping empty pokeset in {}".format(file_obj.name))
                continue
            if prototype:
                raw_pokeset = {**prototype, **raw_pokeset}
            its_notes, pokeset = analyze_pokeset(raw_pokeset)
            notes += its_notes
            if pokeset:
                pokesets.append(pokeset)
    return notes, pokesets


def analyze_pokeset(pokeset):
    notes = []
    identifier = (pokeset.get("species"), pokeset.get("setname"))
    if "ingamename" in pokeset:
        fixed_ingamename = pokeset["ingamename"].encode("ascii", "replace").decode()
        for char in ILLEGAL_CHARS:
            fixed_ingamename = fixed_ingamename.replace(char, "?")
        temp = ""
        for i, char in enumerate(pokeset["ingamename"]):
            if char in ALLOWED_CHARACTERS:
                temp += char
            elif char in NAME_REPLACEMENTS:
                temp += NAME_REPLACEMENTS[char]
            else:
                temp += fixed_ingamename[i]
        fixed_ingamename = temp
        if pokeset["ingamename"] != fixed_ingamename:
            notes.append(Note(
                Severity.NOTE,
                "Changed ingamename to {} to avoid encoding issues".format(fixed_ingamename),
                identifier
            ))
            pokeset["ingamename"] = fixed_ingamename
    with warnings.catch_warnings(record=True) as w:
        try:
            pokeset = pokecat.populate_pokeset(pokeset, skip_ev_check=True)
        except Exception as ex:
            notes.append(Note(
                Severity.ERROR,
                str(ex),  # TODO
                identifier
            ))
        else:
            for warning in w:
                warning_message = str(warning.message)
                notes.append(Note(
                    Severity.WARNING,
                    warning_message,
                    identifier
                ))
            return notes, pokeset
    return notes, None


def analyze_all_pokesets_integrity(original_pokesets):
    notes = []
    pokesets = []
    by_species = lambda p: p["species"]["id"]
    for (species, sets) in groupby(sorted(original_pokesets, key=by_species), key=by_species):
        sets = list(sets)
        species_name = sets[0]["species"]["name"]
        genders = set(chain.from_iterable(p["gender"] for p in sets))
        if None in genders and len(genders) > 1:
            notes.append(Note(
                Severity.ERROR,
                ("Species #{} {} has both genderless and gendered sets! All sets: {}"
                 .format(species, species_name, ", ".join("{} (gender: {})"
                                                          .format(p["setname"], p["gender"]) for p in sets)))
            ))
    existing_ids = set()
    for pokeset in original_pokesets:
        identifier = (pokeset["species"]["id"], pokeset["setname"])
        if identifier in existing_ids:
            notes.append(Note(
                Severity.ERROR,
                ("combination of species {} ({}) and setname {} exists multiple times, but must be unique!"
                 .format(identifier[0], pokeset["species"]["name"], identifier[1])),
                identifier
            ))
        else:
            existing_ids.add(identifier)
            pokesets.append(pokeset)
    return notes, pokesets


def main():
    import json
    notes, pokesets = analyze_dir("./pokesets")
    # filter out low priority notes
    notes = [n for n in notes if n.severity != Severity.NOTE]
    if notes:
        print("==================================== NOTES ====================================")
        for note in notes:
            print(note)
        print("===============================================================================")

    outfile = "pbrpokemondb.json"

    print("Writing compiled sets to {}...".format(outfile))
    with open(outfile, "w+", encoding="utf-8") as f:
        json.dump(pokesets, f, indent="    ", sort_keys=True)

    print("TPP deployment: Place pbrpokemondb.json in tpp/pbrpokemondb.json")

    if notes:
        # some notes existed, return non-zero exit code to indicate failure
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
