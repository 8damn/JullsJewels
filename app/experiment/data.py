"""Sdílená paleta dat pro experimentální vizualizéry konfigurátoru.

Žádné importy z hlavního projektu (modely, DB, ...). Tento modul je
úmyslně samostatný — sandbox pro testování UX přístupů ke konfigurátoru
před tím, než se rozhodne o finální implementaci.
"""

# Cesty ukazují na /static/experiment/beads/ — soubory jsou .svg placeholdery,
# které lze později jednoduše nahradit reálnými fotkami (stejný název, jiná
# přípona není problém — měníme jen <img src="…">).

BEADS_6MM = [
    {"slug": "amethyst",    "name": "Ametyst",     "image": "/static/experiment/beads/6mm-amethyst.svg",    "price": 0},
    {"slug": "labradorite", "name": "Labradorit",  "image": "/static/experiment/beads/6mm-labradorite.svg", "price": 0},
    {"slug": "carnelian",   "name": "Karneol",     "image": "/static/experiment/beads/6mm-carnelian.svg",   "price": 0},
    {"slug": "rosequartz",  "name": "Ruženín",     "image": "/static/experiment/beads/6mm-rosequartz.svg",  "price": 0},
    {"slug": "onyx",        "name": "Onyx",        "image": "/static/experiment/beads/6mm-onyx.svg",        "price": 0},
    {"slug": "aventurine",  "name": "Aventurín",   "image": "/static/experiment/beads/6mm-aventurine.svg",  "price": 0},
]

BEADS_8MM = [
    {"slug": "clearcrystal",  "name": "Křišťál",        "image": "/static/experiment/beads/8mm-clearcrystal.svg",  "price": 30},
    {"slug": "obsidian",      "name": "Obsidián",       "image": "/static/experiment/beads/8mm-obsidian.svg",      "price": 30},
    {"slug": "amethyst-dark", "name": "Ametyst tmavý",  "image": "/static/experiment/beads/8mm-amethyst-dark.svg", "price": 30},
    {"slug": "tigereye",      "name": "Tygří oko",      "image": "/static/experiment/beads/8mm-tigereye.svg",      "price": 30},
]

SEPARATORS = [
    {"slug": "rocaille-silver", "name": "Rokajl stříbrný", "type": "rocaille", "image": "/static/experiment/beads/sep-rocaille-silver.svg", "price": 0},
    {"slug": "rocaille-gold",   "name": "Rokajl zlatý",    "type": "rocaille", "image": "/static/experiment/beads/sep-rocaille-gold.svg",   "price": 0},
    {"slug": "spacer-silver",   "name": "Mezidíl stříbrný","type": "spacer",   "image": "/static/experiment/beads/sep-spacer-silver.svg",   "price": 20},
    {"slug": "spacer-gold",     "name": "Mezidíl zlatý",   "type": "spacer",   "image": "/static/experiment/beads/sep-spacer-gold.svg",     "price": 20},
]

LENGTHS = [
    {"cm": 17, "beadCount": 18, "price": 0},
    {"cm": 19, "beadCount": 20, "price": 30},
    {"cm": 21, "beadCount": 22, "price": 60},
]

# Předvybrané "kolekce" pro V3 Quickpicker
COLLECTIONS = [
    {
        "id": "romantic-dusk",
        "name": "Romantický soumrak",
        "tags": ["jemne", "minimal"],
        "price": 520,
        "pattern": [
            {"role": "main", "bead": "rosequartz"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "main", "bead": "rosequartz"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "main", "bead": "amethyst"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "accent","bead": "amethyst-dark"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "accent","bead": "clearcrystal"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "accent","bead": "amethyst-dark"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "main", "bead": "amethyst"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "main", "bead": "rosequartz"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "main", "bead": "rosequartz"},
        ],
    },
    {
        "id": "earth-warmth",
        "name": "Zemské teplo",
        "tags": ["zemite", "napadne"],
        "price": 560,
        "pattern": [
            {"role": "main", "bead": "carnelian"},
            {"role": "sep",  "bead": "spacer-gold"},
            {"role": "main", "bead": "aventurine"},
            {"role": "sep",  "bead": "spacer-gold"},
            {"role": "main", "bead": "carnelian"},
            {"role": "sep",  "bead": "spacer-gold"},
            {"role": "accent","bead": "tigereye"},
            {"role": "sep",  "bead": "spacer-gold"},
            {"role": "accent","bead": "tigereye"},
            {"role": "sep",  "bead": "spacer-gold"},
            {"role": "accent","bead": "tigereye"},
            {"role": "sep",  "bead": "spacer-gold"},
            {"role": "main", "bead": "carnelian"},
            {"role": "sep",  "bead": "spacer-gold"},
            {"role": "main", "bead": "aventurine"},
            {"role": "sep",  "bead": "spacer-gold"},
            {"role": "main", "bead": "carnelian"},
        ],
    },
    {
        "id": "midnight",
        "name": "Půlnoc",
        "tags": ["tmave", "napadne"],
        "price": 590,
        "pattern": [
            {"role": "main", "bead": "onyx"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "main", "bead": "labradorite"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "main", "bead": "onyx"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "accent","bead": "obsidian"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "accent","bead": "obsidian"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "accent","bead": "obsidian"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "main", "bead": "onyx"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "main", "bead": "labradorite"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "main", "bead": "onyx"},
        ],
    },
    {
        "id": "pastel-mix",
        "name": "Pastelový mix",
        "tags": ["jemne", "napadne"],
        "price": 540,
        "pattern": [
            {"role": "main", "bead": "rosequartz"},
            {"role": "sep",  "bead": "rocaille-gold"},
            {"role": "main", "bead": "aventurine"},
            {"role": "sep",  "bead": "rocaille-gold"},
            {"role": "main", "bead": "amethyst"},
            {"role": "sep",  "bead": "rocaille-gold"},
            {"role": "accent","bead": "clearcrystal"},
            {"role": "sep",  "bead": "rocaille-gold"},
            {"role": "accent","bead": "clearcrystal"},
            {"role": "sep",  "bead": "rocaille-gold"},
            {"role": "accent","bead": "clearcrystal"},
            {"role": "sep",  "bead": "rocaille-gold"},
            {"role": "main", "bead": "amethyst"},
            {"role": "sep",  "bead": "rocaille-gold"},
            {"role": "main", "bead": "aventurine"},
            {"role": "sep",  "bead": "rocaille-gold"},
            {"role": "main", "bead": "rosequartz"},
        ],
    },
    {
        "id": "deep-forest",
        "name": "Hluboký les",
        "tags": ["zemite", "minimal"],
        "price": 530,
        "pattern": [
            {"role": "main", "bead": "aventurine"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "main", "bead": "aventurine"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "main", "bead": "onyx"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "accent","bead": "tigereye"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "accent","bead": "obsidian"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "accent","bead": "tigereye"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "main", "bead": "onyx"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "main", "bead": "aventurine"},
            {"role": "sep",  "bead": "rocaille-silver"},
            {"role": "main", "bead": "aventurine"},
        ],
    },
    {
        "id": "fire-stone",
        "name": "Ohnivý kámen",
        "tags": ["zemite", "napadne"],
        "price": 580,
        "pattern": [
            {"role": "main", "bead": "carnelian"},
            {"role": "sep",  "bead": "spacer-silver"},
            {"role": "main", "bead": "onyx"},
            {"role": "sep",  "bead": "spacer-silver"},
            {"role": "main", "bead": "carnelian"},
            {"role": "sep",  "bead": "spacer-silver"},
            {"role": "accent","bead": "tigereye"},
            {"role": "sep",  "bead": "spacer-silver"},
            {"role": "accent","bead": "obsidian"},
            {"role": "sep",  "bead": "spacer-silver"},
            {"role": "accent","bead": "tigereye"},
            {"role": "sep",  "bead": "spacer-silver"},
            {"role": "main", "bead": "carnelian"},
            {"role": "sep",  "bead": "spacer-silver"},
            {"role": "main", "bead": "onyx"},
            {"role": "sep",  "bead": "spacer-silver"},
            {"role": "main", "bead": "carnelian"},
        ],
    },
]

# Default vzorec pro V1 Photostrand admin (sekvence rolí, ne konkrétních korálků)
DEFAULT_PATTERN_V1 = ["main","sep","main","sep","main","sep","accent","sep","accent","sep","accent","sep","main","sep","main","sep","main"]


def all_beads_flat():
    """Vrátí všechny korálky v jednom seznamu pro JS přenos."""
    out = []
    for b in BEADS_6MM:
        out.append({**b, "size": "6mm", "category": "main"})
    for b in BEADS_8MM:
        out.append({**b, "size": "8mm", "category": "accent"})
    for s in SEPARATORS:
        out.append({**s, "size": "sep", "category": "separator"})
    return out
