#!/usr/bin/env python3
"""party-menu: plan a home dinner for N people from the HowToCook recipes.

  python party_menu.py plan 6 --cook HowToCook/            # three menus: quick, balanced, feast
  python party_menu.py plan 10 --kids --budget 9000 --shop  # + kcal budget and the amounts to buy
Dish counts follow HowToCook's tips/如何选择现在吃什么.md; tiers, per-person totals and the budget
check follow mcd-party-planner's group-meal plans. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

ANIMALS = ("pork", "chicken", "beef", "lamb", "duck", "fish")  # HowToCook's order for meat dishes
# the first animal named wins; bare 肉/排/骨/肠 means pork in Chinese menus only when no animal is named
ANIMAL_RE = {"chicken": "鸡", "beef": "牛", "lamb": "羊", "duck": "鸭", "fish": "鱼", "other": "蛙|兔",
             "pork": "猪|五花|培根|腊肉|腊肠|排骨|里脊|火腿|蹄"}
# like mcd-party-planner's 经济型 / 均衡型 / 丰盛型: each tier adds a course
TIERS = {"quick": (), "balanced": ("soup",), "feast": ("soup", "dessert")}


def dish_counts(n):
    """HowToCook: dishes = people + 1; meat dishes equal to or one more than vegetable dishes."""
    return (n + 1) // 2, (n + 2) // 2  # (vegetable a, meat b): a + b = n + 1, a <= b <= a + 1


def section(lines, title):
    out, inside = [], False
    for line in lines:
        if line.startswith("## "):
            inside = line.strip() == title
        elif inside and line.lstrip().startswith(("* ", "- ")):
            out.append(line.strip()[2:].strip())
    return out


def parse(path, category):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    stars = re.search(r"^预估烹饪难度：\s*(★+)\s*$", text, re.M)
    kcal = re.search(r"^预估卡路里：\s*(\d+)\s*大卡$", text, re.M)
    dish = {"name": path.stem, "category": category, "stars": len(stars.group(1)) if stars else None,
            "kcal": int(kcal.group(1)) if kcal else None, "path": path.as_posix(),
            "ingredients": section(lines, "## 必备原料和工具"), "amounts": section(lines, "## 计算")}
    dish["animal"] = animal_of(dish)
    return dish


def animal_of(dish):
    if dish["category"] == "aquatic":
        return "fish" if "鱼" in dish["name"] else "seafood"
    if dish["category"] != "meat_dish":
        return None
    for text in (dish["name"], " ".join(dish["ingredients"])):  # the name decides first
        # eggs, seasonings and (brand / alternative) notes are not the dish's animal
        text = re.sub(r"鸡蛋|鸭蛋|鸡精|鸡粉|牛奶|牛油|鱼香|鱼露|（[^）]*）|\([^)]*\)", "", text.replace("牛蛙", "蛙"))
        hits = [(m.start(), animal) for animal, words in ANIMAL_RE.items() if (m := re.search(words, text))]
        if hits:
            return min(hits)[1]
        if re.search("肉|排|骨|肠", text):
            return "pork"
    return "other"


def load(root):
    root = Path(root) / "dishes"
    if not root.is_dir():
        raise SystemExit(f"party-menu: {root} not found; pass --cook PATH/TO/HowToCook")
    return [parse(p, p.relative_to(root).parts[0]) for p in sorted(root.rglob("*.md"))
            if p.relative_to(root).parts[0] != "template"]


def ordered(dishes, tier, rng):
    """quick: easiest first, feast: hardest first, balanced: closest to 3 stars. Ties shuffled by seed."""
    key = {"quick": lambda d: d["stars"], "feast": lambda d: -d["stars"], "balanced": lambda d: abs(d["stars"] - 3)}[tier]
    pool = [d for d in dishes if d["stars"] and d["kcal"]]
    rng.shuffle(pool)
    return sorted(pool, key=key)


def pick_meat(pool, b, need_fish):
    """Round-robin over HowToCook's animal order, so no animal repeats until every one is used; fish first if needed."""
    queues = {}
    for d in pool:
        queues.setdefault(d["animal"], []).append(d)
    order = [a for a in (*ANIMALS, "seafood", "other") if a in queues]
    if need_fish and "fish" in order:
        order.insert(0, order.pop(order.index("fish")))
    picks = []
    while len(picks) < b and any(queues[a] for a in order):
        for a in order:
            if queues[a] and len(picks) < b:
                picks.append(queues[a].pop(0))
    return picks


def plan(dishes, people, budget=0, kids=False, seed=0):
    if people <= 0:
        raise ValueError("people must be a positive integer")
    if budget < 0:
        raise ValueError("budget cannot be negative")
    a, b = dish_counts(people)
    plans = []
    for tier, extra in TIERS.items():
        pool = ordered(dishes, tier, random.Random(seed))
        cat = lambda *cs: [d for d in pool if d["category"] in cs]  # noqa: E731
        picked = cat("vegetable_dish")[:a] + pick_meat(cat("meat_dish", "aquatic"), b, people > 8)
        courses = list(extra) + (["dessert"] if kids and "dessert" not in extra else [])
        picked += [cat(c)[0] for c in courses if cat(c)]
        total = sum(d["kcal"] for d in picked)
        plans.append({"tier": tier, "dishes": picked, "total": total,
                      "perPerson": round(total / people, 2),
                      "withinBudget": total <= budget if budget else True,
                      "stars": sum(d["stars"] for d in picked)})
    best = min(plans, key=lambda p: (not p["withinBudget"], p["perPerson"]))  # mcd-party-planner's pick
    return {"people": people, "vegetable": a, "meat": b, "budget": budget, "plans": plans,
            "recommended": best["tier"], "affordableCount": sum(p["withinBudget"] for p in plans)}


def render(result, shop=False):
    out = [f"{result['people']} people -> {result['vegetable']} vegetable + {result['meat']} meat dishes"
           + (f", budget {result['budget']} kcal" if result["budget"] else "")]
    for p in result["plans"]:
        flag = "" if not result["budget"] else ("  within budget" if p["withinBudget"] else "  OVER budget")
        out.append(f"\n[{p['tier']}] {p['total']} kcal, {p['perPerson']} kcal/person, {p['stars']} stars of work{flag}")
        for d in p["dishes"]:
            out.append(f"  {'*' * d['stars']:<5} {d['kcal']:>5} kcal  {d['name']} ({d['category']}{', ' + d['animal'] if d['animal'] else ''})")
            if shop:
                out += [f"          - {x}" for x in d["amounts"] or d["ingredients"]]
    out.append(f"\nRecommended: {result['recommended']} ({result['affordableCount']} of 3 within budget)")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="party-menu", description="Plan a home dinner from HowToCook recipes.")
    ap.add_argument("action", choices=["plan", "dishes"])
    ap.add_argument("people", type=int, nargs="?", default=4)
    ap.add_argument("--cook", default="HowToCook", help="path to a HowToCook checkout (default ./HowToCook)")
    ap.add_argument("--budget", type=float, default=0, help="total kcal budget for the table (0 = none)")
    ap.add_argument("--kids", action="store_true", help="add a sweet dish (HowToCook: if children come)")
    ap.add_argument("--seed", type=int, default=0, help="shuffle dishes of equal difficulty differently")
    ap.add_argument("--shop", action="store_true", help="list the amounts to buy under each dish")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    dishes = load(a.cook)
    if a.action == "dishes":
        for d in dishes:
            print(json.dumps({k: d[k] for k in ("name", "category", "stars", "kcal", "animal")}, ensure_ascii=False))
        return 0
    result = plan(dishes, a.people, a.budget, a.kids, a.seed)
    if a.json:
        for p in result["plans"]:
            p["dishes"] = [d["name"] for d in p["dishes"]]
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        print(render(result, a.shop))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
