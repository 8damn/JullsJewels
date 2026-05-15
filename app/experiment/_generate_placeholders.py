"""Jednorázový skript: vygeneruje 14 SVG placeholder fotek korálků.

Spuštění (z adresáře jullsjewels/):
    python -m app.experiment._generate_placeholders

Výsledek se zapíše do app/static/experiment/beads/.
Skript je idempotentní — můžeš spustit kolikrát chceš.

Reálné fotky korálků uživatelky později nahradí tyto soubory
(stejný název, jakákoliv přípona — vizualizéry čtou skrz <img src=...>).
"""

from pathlib import Path

OUT_DIR = Path("app/static/experiment/beads")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def bead_svg(highlight_color: str, mid_color: str, dark_color: str) -> str:
    """Kulatý korálek s radial gradientem a leskem — vypadá jako fotka."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <radialGradient id="g" cx="35%" cy="35%" r="65%">
      <stop offset="0%" stop-color="{highlight_color}"/>
      <stop offset="55%" stop-color="{mid_color}"/>
      <stop offset="100%" stop-color="{dark_color}"/>
    </radialGradient>
  </defs>
  <circle cx="50" cy="50" r="48" fill="url(#g)"/>
  <ellipse cx="38" cy="33" rx="13" ry="8" fill="white" opacity="0.45"/>
  <ellipse cx="35" cy="32" rx="6" ry="3" fill="white" opacity="0.8"/>
  <circle cx="50" cy="50" r="48" fill="none" stroke="rgba(0,0,0,0.18)" stroke-width="1"/>
</svg>
'''


def rocaille_svg(color_main: str, color_dark: str) -> str:
    """Drobný rokajlový korálek — taky kulatý, ale plošší (méně lesku, menší proporce)."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <radialGradient id="g" cx="40%" cy="40%" r="60%">
      <stop offset="0%" stop-color="{color_main}"/>
      <stop offset="100%" stop-color="{color_dark}"/>
    </radialGradient>
  </defs>
  <circle cx="50" cy="50" r="46" fill="url(#g)"/>
  <ellipse cx="40" cy="38" rx="10" ry="6" fill="white" opacity="0.55"/>
  <circle cx="50" cy="50" r="46" fill="none" stroke="rgba(0,0,0,0.25)" stroke-width="1.2"/>
</svg>
'''


def spacer_svg(color_main: str, color_dark: str) -> str:
    """Kovový mezidíl — plochý disk, vypadá jako z boku."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{color_dark}"/>
      <stop offset="15%" stop-color="{color_main}"/>
      <stop offset="50%" stop-color="white" stop-opacity="0.7"/>
      <stop offset="85%" stop-color="{color_main}"/>
      <stop offset="100%" stop-color="{color_dark}"/>
    </linearGradient>
  </defs>
  <rect x="6" y="38" width="88" height="24" rx="3" fill="url(#g)" stroke="rgba(0,0,0,0.3)" stroke-width="1"/>
  <line x1="10" y1="42" x2="90" y2="42" stroke="white" stroke-width="0.7" opacity="0.6"/>
  <line x1="10" y1="58" x2="90" y2="58" stroke="rgba(0,0,0,0.15)" stroke-width="0.7"/>
</svg>
'''


BEADS = {
    # 6mm hlavní korálky (minerální)
    "6mm-amethyst.svg":     bead_svg("#e8d4f0", "#9b59b6", "#4a235a"),
    "6mm-labradorite.svg":  bead_svg("#b8c5d6", "#6c7a89", "#2c3e50"),
    "6mm-carnelian.svg":    bead_svg("#fce4d4", "#d35400", "#7d2e0e"),
    "6mm-rosequartz.svg":   bead_svg("#fce4ea", "#f1948a", "#a04a3f"),
    "6mm-onyx.svg":         bead_svg("#5a5a5a", "#1a1a1a", "#000000"),
    "6mm-aventurine.svg":   bead_svg("#c8e6c9", "#52a86b", "#1b5e20"),

    # 8mm akcentové
    "8mm-clearcrystal.svg":   bead_svg("#ffffff", "#e8eef3", "#a8b5c3"),
    "8mm-obsidian.svg":       bead_svg("#4a4a4a", "#1c2833", "#000000"),
    "8mm-amethyst-dark.svg":  bead_svg("#a872c0", "#6c3483", "#3b1850"),
    "8mm-tigereye.svg":       bead_svg("#f5d189", "#b87333", "#5e3a0f"),

    # Separátory — rokajl
    "sep-rocaille-silver.svg":  rocaille_svg("#e8e8e8", "#8a8a8a"),
    "sep-rocaille-gold.svg":    rocaille_svg("#f4d77f", "#9c7a1a"),

    # Separátory — kovový mezidíl
    "sep-spacer-silver.svg":    spacer_svg("#c0c0c0", "#5a5a5a"),
    "sep-spacer-gold.svg":      spacer_svg("#d4ac0d", "#8a6e0a"),
}


def main():
    for filename, content in BEADS.items():
        path = OUT_DIR / filename
        path.write_text(content, encoding="utf-8")
        print(f"  [ok] {path}")
    print(f"\nVygenerovano {len(BEADS)} SVG souboru do {OUT_DIR}/")


if __name__ == "__main__":
    main()
