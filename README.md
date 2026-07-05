# joujou-erdos-unit-distance
Faire jou-jou avec le problème de la distance unitaire d'Erdos

## Générer un GIF d'animation

Script: `/home/runner/work/joujou-erdos-unit-distance/joujou-erdos-unit-distance/generate_unit_distance_gif.py`

Exemple (grille 16x16 par défaut):

```bash
python generate_unit_distance_gif.py --output erdos_unit_distance.gif
```

Options utiles:
- `--grid-size` (défaut `16`)
- `--fps` (défaut `2`)
- `--include-non-pertinent` pour inclure aussi les maillages sans paire à distance 1
