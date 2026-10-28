---
name: party-menu
description: Plan what to cook for a group from the HowToCook recipe collection. Picks the number of vegetable and meat dishes for the head count, avoids repeating the same meat, adds fish for big groups and a sweet dish for children, and gives three menus (quick, balanced, feast) with calories per person, a kcal budget check and the amounts to buy. Use for "what should I cook for 6 people", "dinner party menu", "plan a family meal".
---

# party-menu

Turns HowToCook's rule for choosing dishes into a menu. Python 3.9+, standard library only. Needs a HowToCook checkout:

```bash
git clone --depth 1 https://github.com/Anduin2017/HowToCook
```

## Commands (run from the repo root)

```bash
python party_menu.py plan 6                           # 3 menus for 6 people (looks for ./HowToCook)
python party_menu.py plan 10 --kids --budget 9000     # big group: fish first, a dessert, 9000 kcal for the table
python party_menu.py plan 4 --shop                    # add the amounts from each recipe's calculation section
python party_menu.py plan 4 --seed 3                  # another menu: shuffles dishes of equal difficulty
python party_menu.py plan 4 --json                    # machine-readable
python party_menu.py dishes --cook PATH/TO/HowToCook  # every recipe with stars, kcal and main meat
```

## How it chooses
- Dishes = people + 1; meat dishes equal to or one more than vegetable dishes (HowToCook tips).
- Meat dishes rotate pork, chicken, beef, lamb, duck, fish, so no meat repeats until each kind is used. More than 8 people: a fish dish first. `--kids`: a dessert.
- quick = easiest dishes, balanced = closest to 3 stars plus a soup, feast = hardest dishes plus a soup and a dessert.
- Calories and difficulty come from each recipe's own header lines. They are the recipe authors' estimates for one batch.

## Rules
- Show the recipe file path when the user wants to cook a dish; the steps are in that file.
- Recipe names and amounts are in Chinese; translate them for the user if they do not read Chinese.
