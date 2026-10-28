<div align="center">

# party-menu

**Plan a home dinner for N people from the 370 HowToCook recipes: three menus, calories per person, a shopping list.**

HowToCook (100k+ stars) writes down the rule for choosing dishes, then tells you to pick them by hand. party-menu does the picking, the way mcd-party-planner builds group meals: three tiers, per-person totals, a budget check.

Works with **Claude Code** and **Codex**.

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg) ![Status: prototype](https://img.shields.io/badge/status-prototype-orange.svg)

</div>

## Quick start
```bash
git clone https://github.com/Dodai0419/party-menu && cd party-menu
git clone --depth 1 https://github.com/Anduin2017/HowToCook
python party_menu.py plan 6 --budget 8000
```
Dish names come from HowToCook, which is written in Chinese:
```
6 people -> 3 vegetable + 4 meat dishes, budget 8000.0 kcal

[quick] 7156 kcal, 1192.67 kcal/person, 15 stars of work  within budget
  *       566 kcal  皮蛋豆腐 (vegetable_dish)
  *       107 kcal  凉拌黄瓜 (vegetable_dish)
  *       391 kcal  炒滑蛋 (vegetable_dish)
  *      1030 kcal  黔式腊肠娃娃菜 (meat_dish, pork)
  **      850 kcal  葱烧鸡腿 (meat_dish, chicken)
  ****   1821 kcal  咖喱肥牛 (meat_dish, beef)
  *****  2391 kcal  枝竹羊腩煲 (meat_dish, lamb)

[balanced] 8230 kcal, 1371.67 kcal/person, 27 stars of work  OVER budget
...
Recommended: quick (1 of 3 within budget)
```
No clone at hand? `python party_menu.py plan 6 --cook tests/fixtures` runs on the 15 recipes bundled for tests. Python 3.9+, standard library only.

## The problem
- "What do we cook for 6 people?" HowToCook answers with a formula (dishes = people + 1, meat equal to or one more than vegetables, no meat twice, fish for big groups) that you still apply by hand.
- 370 recipes carry a difficulty and a calorie line in their headers, but nothing adds them up for a whole table.
- Group meal planners such as mcd-party-planner compare tiers and per-person totals, but only for one restaurant's menu and only with an API token.

## The solution
| Idea | Fixes |
|------|-------|
| **HowToCook's rule as code**: dish counts for the head count, meats rotated pork, chicken, beef, lamb, duck, fish; fish first above 8 people; a dessert with `--kids` | The menu follows the cookbook's own advice, every time |
| **Three tiers** (mcd-party-planner's economy / balanced / rich): quick = easiest dishes, balanced = about 3 stars plus a soup, feast = hardest plus soup and dessert | Choose by effort, not by scrolling 370 files |
| **Totals and a budget**: kcal for the table and per person, `--budget` flags menus over it, the menu within budget with the fewest kcal per person is recommended (mcd-party-planner's rule) | One look tells you which menu fits |
| **`--shop`**: each dish's amounts from its calculation section | The shopping list without opening every recipe |

`--seed N` shuffles dishes of equal difficulty for a different menu; `--json` for scripts.

## Use with Claude Code
```bash
/plugin marketplace add Dodai0419/party-menu
/plugin install party-menu@party-menu
```
Then ask: "plan dinner for 6 people, two of them kids, under 9000 kcal".

## Use with Codex (ChatGPT)
```bash
git clone https://github.com/Dodai0419/party-menu && cp -r party-menu/skills/* ~/.codex/skills/
```
Or copy `AGENTS.md` into your project root.

## Benchmarks
Windows 11, Python 3.11.1, Node 24.20.0. HowToCook `f6da452` (372 recipes outside `template/`), mcd-party-planner `9af9061`. Command: `python bench/bench.py PATH/TO/HowToCook`.

| | sources | party-menu |
|---|---|---|
| dish counts for 1..100 people | HowToCook's formula, run in node | identical |
| plan 3 menus for 10 people | by hand (HowToCook); mcd-party-planner needs a McDonald's MCP token and the network, so it cannot plan a home meal | 0.2-0.6 s, including reading all 372 recipes (medians of 7 runs: 334, 523, 623 ms on 2026-10-21; 181-217 ms on F's run) |
| lines of code | mcd-party-planner `party_planner.py` 508 | `party_menu.py` 161 |
| dependencies | 0 (both) | 0 |
| tests | mcd-party-planner: 40 pass offline | 10 pass |

Most of that time is opening 372 files on Windows, so it swings with the disk cache (profiled: `io.open` 179 ms of one load).

## Inspired by
- [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook): the recipes, their difficulty and calorie lines, and the rule in `tips/如何选择现在吃什么.md` for how many and which dishes to cook.
- [zcbacxc/mcd-party-planner](https://github.com/zcbacxc/mcd-party-planner): tiers that add a course each, per-person totals, the budget flag and the recommendation rule.

## Roadmap
- [ ] Sum amounts across dishes (HowToCook writes them per recipe in free text).
- [ ] Keep a "cooked recently" list so the next menu changes.
- [ ] English dish names from HowToCook's translation work, when it lands.

## License
MIT. Bundled test recipes are from HowToCook (The Unlicense).
