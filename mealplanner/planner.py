"""Filtering, random selection, and re-roll logic for weekly meal plans."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .models import Meal


@dataclass
class Config:
    num_meals: int = 5
    include_proteins: set[str] | None = None  # None = allow any protein
    exclude_proteins: set[str] = field(default_factory=set)
    efforts: set[str] | None = None  # None = allow any effort level
    min_vegetarian: int = 0  # at least this many selected meals must be vegetarian
    leftovers_only: bool = False


def filter_meals(meals: list[Meal], config: Config) -> list[Meal]:
    result = []
    for meal in meals:
        if config.leftovers_only and not meal.leftovers:
            continue
        if config.efforts and meal.effort not in config.efforts:
            continue
        if config.include_proteins and meal.protein not in config.include_proteins:
            continue
        if meal.protein in config.exclude_proteins:
            continue
        result.append(meal)
    return result


def select_week(
    meals: list[Meal], config: Config, rng: random.Random | None = None
) -> list[Meal]:
    """Randomly pick `config.num_meals` distinct meals matching the criteria.

    At least `config.min_vegetarian` of the picks will be vegetarian.
    """
    rng = rng or random.Random()
    pool = filter_meals(meals, config)
    if len(pool) < config.num_meals:
        raise ValueError(
            f"Not enough meals match the criteria: need {config.num_meals}, found {len(pool)}"
        )
    veg_pool = [m for m in pool if m.vegetarian]
    if len(veg_pool) < config.min_vegetarian:
        raise ValueError(
            f"Not enough vegetarian meals match the criteria: "
            f"need {config.min_vegetarian}, found {len(veg_pool)}"
        )
    required_veg = rng.sample(veg_pool, config.min_vegetarian)
    required_names = {m.name for m in required_veg}
    remaining_pool = [m for m in pool if m.name not in required_names]
    rest = rng.sample(remaining_pool, config.num_meals - config.min_vegetarian)
    selection = required_veg + rest
    rng.shuffle(selection)
    return selection


def reroll_meal(
    meals: list[Meal],
    config: Config,
    current_selection: list[Meal],
    index: int,
    rng: random.Random | None = None,
) -> list[Meal]:
    """Replace the meal at `index` with a new random pick that isn't already selected.

    If the current meal is vegetarian and removing it would drop the selection
    below `config.min_vegetarian`, the replacement is restricted to vegetarian meals.
    """
    rng = rng or random.Random()
    pool = filter_meals(meals, config)
    current = current_selection[index]
    other_names = {m.name for i, m in enumerate(current_selection) if i != index}
    # Must differ from the current meal; only avoid duplicating other selections when possible.
    non_current = [m for m in pool if m.name != current.name]
    current_veg_count = sum(1 for m in current_selection if m.vegetarian)
    if current.vegetarian and current_veg_count <= config.min_vegetarian:
        non_current = [m for m in non_current if m.vegetarian]
    if not non_current:
        raise ValueError(
            "No alternative meals available for re-roll with the current criteria"
        )
    candidates = [m for m in non_current if m.name not in other_names]
    chosen_pool = candidates or non_current

    new_selection = list(current_selection)
    new_selection[index] = rng.choice(chosen_pool)
    return new_selection
