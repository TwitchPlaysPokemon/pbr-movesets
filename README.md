# pbr-movesets

## What are the .YAML Files?
The .YAML files within this repository are all to help inject Pokemon within Twitch Plays Pokemon, Battle Revolution.
## Making the .YAML Files
A blank Pokemon .YAML file will generally look like this (may vary depending on meta/tags):
```
species:
setname:
tags: []
item: []
ability: []
moves:
    - []
    - []
    - []
    - []
combinations:
    - []
separations:
    - []
gender: [m, f]
happiness: 255
biddable: True
rarity: 1.0
ball: []
nature:
ivs: {hp: , atk: , def: , spA: , spD: , spe: }
evs: {hp: , atk: , def: , spA: , spD: , spe: }
```

### Things NOT necessary to include:
- __Shiny__ 
  - _Hidden goes with Shiny._
- __Ingamename and displayname__ 
  - _Both only added if a nickname exceeds the maximum of 10 Characters for ingamename._)
- __Additions + suppressions__ 
  - _If there aren't any._
- __Levels__ 
  - _Unless if they differ from the standard Level 100._

### Things that ARE necessary to include:
- __Species__
   - _All of one species for a meta would be included within the same file._
- __Setname__
  - _There can't be any of the same setnames._
- __Tags__
  - _Usually just the meta tag._
- __Items__
  - _Put [null] if there is none._
- __Ability__ 
  - _Put [null] if there is none._
- __Moves__
  - _If there are less than 4 moves, don't include any after the ones it has._
- __Gender__
  - _If there is no gender, do not include._
- __Happiness__
  - _Default 255, max_
- __Biddable__
  - _Yes or No._
- __Rarity__
  - _0.0 means it does not appear within matchmaking._
- __Ball__
  - _No apricot balls._
- __Nature__
  - _Put [null] if there is none_.
- __IVS + EVS__
  - _If there's all of one (for example, something has all 31 IVs), you can put the number itself instead of the full format._

## Editing .YAMLS Efficiently
Download the [Github desktop app](https://desktop.github.com/) and [Atom](https://atom.io/). Using the Github app, simply copy the repository for pbr-movesets. You can then open in Atom to mass edit / upload / etc. multiple files. Once you update something, save your changes on Atom and it will show on the Github app. Only thing left is to remember to title your changes and to actually commit them to the repository (under the master branch).

---
__If there are any questions regarding anything, feel free to ask.__
