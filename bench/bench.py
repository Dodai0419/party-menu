"""python bench/bench.py PATH/TO/HowToCook

1. HowToCook's own formula (tips/如何选择现在吃什么.md, run in node) vs dish_counts for 1..100 people.
2. Time to load every HowToCook recipe and plan all three menus, median of 7 runs.
"""
import json
import os
import statistics
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import party_menu  # noqa: E402

root = sys.argv[1]
js = ("const r=[];for(let N=1;N<=100;N++){const a=Math.floor((N+1)/2);const b=Math.ceil((N+1)/2);r.push([a,b])}"
      "console.log(JSON.stringify(r))")
upstream = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True).stdout)
ours = [list(party_menu.dish_counts(n)) for n in range(1, 101)]
print("dish counts identical to HowToCook formula for 1..100 people:", upstream == ours)

times = []
for _ in range(7):
    t = time.perf_counter()
    dishes = party_menu.load(root)
    result = party_menu.plan(dishes, 10, budget=9000, kids=True)
    times.append((time.perf_counter() - t) * 1000)
print(f"{len(dishes)} recipes loaded and 3 menus planned for 10 people: median {statistics.median(times):.1f} ms")
