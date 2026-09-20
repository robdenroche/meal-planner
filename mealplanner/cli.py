"""Interactive terminal entry point for trying out the meal planner locally."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from .models import Meal, load_meals
from .planner import Config, reroll_meal, select_week
from .shopping_list import build_shopping_list


def _print_meal(index: int, meal: Meal) -> None:
    tags = [meal.effort, meal.protein]
    if meal.vegetarian:
        tags.append("vegetarian")
    if meal.leftovers:
        tags.append("leftovers")
    tag_str = ", ".join(t for t in tags if t)
    print(f"  [{index}] {meal.name} ({tag_str})")
    print(f"      ingredients: {', '.join(meal.ingredients)}")
    if meal.recipe:
        print(f"      recipe: {meal.recipe}")


def _print_shopping_list(meals: list[Meal]) -> None:
    print("\nShopping list:")
    for item in build_shopping_list(meals):
        meal_list = ", ".join(item["meals"])
        print(f"  - {item['ingredient']} ({meal_list})")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Generate and refine a weekly meal plan."
    )
    parser.add_argument(
        "--meals",
        type=Path,
        default=Path("mains.yaml"),
        help="Path to the meals YAML file.",
    )
    parser.add_argument("--num-meals", type=int, default=5)
    parser.add_argument(
        "--include-protein", action="append", default=None, help="Repeatable."
    )
    parser.add_argument(
        "--exclude-protein", action="append", default=[], help="Repeatable."
    )
    parser.add_argument("--effort", action="append", default=None, help="Repeatable.")
    parser.add_argument("--min-vegetarian", type=int, default=0)
    parser.add_argument("--leftovers-only", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args(argv)

    meals = load_meals(args.meals.read_text())
    config = Config(
        num_meals=args.num_meals,
        include_proteins=set(args.include_protein) if args.include_protein else None,
        exclude_proteins=set(args.exclude_protein),
        efforts=set(args.effort) if args.effort else None,
        min_vegetarian=args.min_vegetarian,
        leftovers_only=args.leftovers_only,
    )
    rng = random.Random(args.seed)

    selection = select_week(meals, config, rng=rng)

    while True:
        print("\nThis week's meals:")
        for i, meal in enumerate(selection):
            _print_meal(i, meal)

        choice = input(
            "\nReroll a meal number, or press Enter to lock in the week: "
        ).strip()
        if not choice:
            break
        try:
            index = int(choice)
            selection = reroll_meal(meals, config, selection, index=index, rng=rng)
        except (ValueError, IndexError) as exc:
            print(f"  Could not reroll: {exc}")

    _print_shopping_list(selection)


if __name__ == "__main__":
    main()
