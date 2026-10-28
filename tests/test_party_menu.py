import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import party_menu as pm  # noqa: E402

FIX = os.path.join(HERE, "tests", "fixtures")
DISHES = pm.load(FIX)
BY_NAME = {d["name"]: d for d in DISHES}


class HowToCookRules(unittest.TestCase):
    def test_dish_counts_match_tips_formula(self):
        for n in range(1, 101):  # a = floor((N+1)/2), b = ceil((N+1)/2)
            a, b = pm.dish_counts(n)
            self.assertEqual((a, b), ((n + 1) // 2, -(-(n + 1) // 2)))
            self.assertEqual(a + b, n + 1)
            self.assertTrue(a <= b <= a + 1)

    def test_parse_recipe_metadata(self):
        d = BY_NAME["可乐鸡翅"]
        self.assertEqual((d["category"], d["stars"], d["kcal"], d["animal"]), ("meat_dish", 3, 960, "chicken"))
        self.assertIn("鸡翅中", d["ingredients"])
        self.assertIn("可乐 500ml", d["amounts"])
        self.assertNotIn("示例菜", BY_NAME)  # template skipped

    def test_animals(self):
        self.assertNotEqual(BY_NAME["尖叫牛蛙"]["animal"], "beef")  # bullfrog is not beef
        self.assertEqual(BY_NAME["西红柿牛腩"]["animal"], "beef")
        self.assertEqual(BY_NAME["红烧鱼"]["animal"], "fish")
        self.assertEqual(BY_NAME["白灼虾"]["animal"], "seafood")
        self.assertIsNone(BY_NAME["凉拌黄瓜"]["animal"])

    def test_generic_pork_characters_do_not_beat_the_named_animal(self):
        # names and ingredient lines as they appear in HowToCook 0e106ee
        cases = {("酱牛肉", "牛腱子"): "beef", ("牛排", "牛排"): "beef", ("煎烤羊排", "羊排"): "lamb",
                 ("无骨鸡爪", "鸡爪"): "chicken", ("鱼香肉丝", "猪里脊肉"): "pork", ("尖叫牛蛙", "牛蛙"): "other",
                 ("冷吃兔", "兔肉"): "other",
                 ("麻婆豆腐", "内脂豆腐 咸鸭蛋（推荐留夫鸭的，这个是灵魂） 五花肉（超市的肉糜也行）"): "pork",
                 ("蚂蚁上树", "红薯粉丝 猪肉末（或牛肉末）"): "pork"}
        for (name, ingredients), want in cases.items():
            dish = {"name": name, "category": "meat_dish", "ingredients": [ingredients]}
            self.assertEqual(pm.animal_of(dish), want, name)

    def test_no_animal_repeats_while_another_is_unused(self):
        have = {d["animal"] for d in DISHES if d["category"] in ("meat_dish", "aquatic") and d["stars"] and d["kcal"]}
        for people in range(1, 21):
            for seed in range(10):
                for p in pm.plan(DISHES, people, seed=seed)["plans"]:
                    animals = [d["animal"] for d in p["dishes"] if d["category"] in ("meat_dish", "aquatic")]
                    if len(animals) != len(set(animals)):
                        self.assertEqual(set(animals), have, (people, seed, p["tier"]))

    def test_no_animal_twice_until_all_used(self):
        for p in pm.plan(DISHES, 6)["plans"]:
            animals = [d["animal"] for d in p["dishes"] if d["category"] in ("meat_dish", "aquatic")]
            self.assertEqual(len(animals), 4)
            self.assertEqual(len(set(animals)), 4)
            self.assertEqual(animals[:2], ["pork", "chicken"])  # HowToCook's order

    def test_more_than_8_people_gets_fish_and_kids_get_dessert(self):
        meat = lambda p: [d["animal"] for d in p["dishes"] if d["animal"]]  # noqa: E731
        for p in pm.plan(DISHES, 9, kids=True)["plans"]:
            self.assertEqual(meat(p)[0], "fish")
            self.assertIn("dessert", [d["category"] for d in p["dishes"]])
        self.assertEqual(meat(pm.plan(DISHES, 8)["plans"][0])[0], "pork")


class PartyPlannerRules(unittest.TestCase):
    def test_tiers_add_courses(self):
        tiers = {p["tier"]: [d["category"] for d in p["dishes"]] for p in pm.plan(DISHES, 4)["plans"]}
        self.assertNotIn("soup", tiers["quick"])
        self.assertIn("soup", tiers["balanced"])
        self.assertTrue({"soup", "dessert"} <= set(tiers["feast"]))

    def test_per_person_budget_and_recommendation(self):
        r = pm.plan(DISHES, 6, budget=7000)
        for p in r["plans"]:
            self.assertEqual(p["perPerson"], round(p["total"] / 6, 2))
            self.assertEqual(p["withinBudget"], p["total"] <= 7000)
        best = sorted(r["plans"], key=lambda p: (not p["withinBudget"], p["perPerson"]))[0]
        self.assertEqual(r["recommended"], best["tier"])
        self.assertEqual(r["affordableCount"], sum(p["withinBudget"] for p in r["plans"]))
        self.assertTrue(all(p["withinBudget"] for p in pm.plan(DISHES, 6)["plans"]))  # 0 = no budget

    def test_bad_input(self):
        with self.assertRaises(ValueError):
            pm.plan(DISHES, 0)
        with self.assertRaises(ValueError):
            pm.plan(DISHES, 3, budget=-1)

    def test_quick_is_easiest(self):
        plans = {p["tier"]: p for p in pm.plan(DISHES, 6)["plans"]}
        self.assertLess(plans["quick"]["stars"], plans["feast"]["stars"])


class Cli(unittest.TestCase):
    def test_plan_output(self):
        out = subprocess.run([sys.executable, os.path.join(HERE, "party_menu.py"), "plan", "6", "--cook", FIX,
                              "--budget", "7000", "--shop"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("6 people -> 3 vegetable + 4 meat dishes", out.stdout)
        self.assertIn("OVER budget", out.stdout)
        self.assertIn("- 可乐 500ml", out.stdout)


if __name__ == "__main__":
    unittest.main()
