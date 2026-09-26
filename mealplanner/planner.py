"""Filtering, random selection, and re-roll logic for weekly meal plans."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .models import Meal

RED_MEAT_PROTEINS = frozenset({"beef", "lamb"})


@dataclass
class Config:
    num_meals: int = 5
    include_proteins: set[str] | None = None  # None = allow any protein
    exclude_proteins: set[str] = field(default_factory=set)
    efforts: set[str] | None = None  # None = allow any effort level
    min_vegetarian: int = 0  # Minimum number of selected vegetarian meals.
    leftovers_only: bool = False
    forced_meals: set[str] = field(default_factory=set)
    max_red_meat_meals: int | None = None


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
    """Randomly pick distinct meals matching the criteria.

    Forced meals are included regardless of other filters. At least
    ``config.min_vegetarian`` selected meals will be vegetarian.
    """
    rng = rng or random.Random()
    forced = [meal for meal in meals if meal.name in config.forced_meals]
    forced_names = {meal.name for meal in forced}
    unknown_forced = config.forced_meals - forced_names
    if unknown_forced:
        unknown_names = ", ".join(sorted(unknown_forced))
        raise ValueError(f"Unknown forced meals: {unknown_names}")
    if len(forced) > config.num_meals:
        raise ValueError(
            f"Too many forced meals: {len(forced)} selected, "
            f"but only {config.num_meals} meals requested"
        )
    if config.max_red_meat_meals is not None and config.max_red_meat_meals < 0:
        raise ValueError("Maximum red meat meals cannot be negative")

    forced_red_meat_count = sum(_is_red_meat_meal(meal) for meal in forced)
    if (
        config.max_red_meat_meals is not None
        and forced_red_meat_count > config.max_red_meat_meals
    ):
        raise ValueError(
            f"Too many forced red meat meals: {forced_red_meat_count} "
            f"selected, but the maximum is {config.max_red_meat_meals}"
        )

    pool = [
        meal for meal in filter_meals(meals, config) if meal.name not in forced_names
    ]
    remaining_count = config.num_meals - len(forced)
    if len(pool) < remaining_count:
        raise ValueError(
            "Not enough meals match the criteria: "
            f"need {remaining_count} more, found {len(pool)}"
        )

    vegetarian_pool = [meal for meal in pool if meal.vegetarian]
    required_vegetarian_count = max(
        0, config.min_vegetarian - sum(meal.vegetarian for meal in forced)
    )
    if len(vegetarian_pool) < required_vegetarian_count:
        raise ValueError(
            "Not enough vegetarian meals match the criteria: "
            f"need {required_vegetarian_count} more, "
            f"found {len(vegetarian_pool)}"
        )

    if config.max_red_meat_meals is not None:
        additional = _select_with_red_meat_limit(
            pool,
            remaining_count,
            required_vegetarian_count,
            config.max_red_meat_meals - forced_red_meat_count,
            rng,
        )
        selection = forced + additional
        rng.shuffle(selection)
        return selection

    required_vegetarian = rng.sample(vegetarian_pool, required_vegetarian_count)
    required_names = {meal.name for meal in required_vegetarian}
    remaining_pool = [meal for meal in pool if meal.name not in required_names]
    rest = rng.sample(remaining_pool, remaining_count - required_vegetarian_count)
    selection = forced + required_vegetarian + rest
    rng.shuffle(selection)
    return selection


def _is_red_meat_meal(meal: Meal) -> bool:
    if meal.protein is None:
        return False
    proteins = {protein.strip().lower() for protein in meal.protein.split("/")}
    return bool(RED_MEAT_PROTEINS & proteins)


def _select_with_red_meat_limit(
    pool: list[Meal],
    count: int,
    vegetarian_count: int,
    red_meat_slots: int,
    rng: random.Random,
) -> list[Meal]:
    red_meat_vegetarian = [
        meal for meal in pool if _is_red_meat_meal(meal) and meal.vegetarian
    ]
    other_vegetarian = [
        meal for meal in pool if not _is_red_meat_meal(meal) and meal.vegetarian
    ]
    other_vegetarian_count = min(vegetarian_count, len(other_vegetarian))
    red_meat_vegetarian_count = vegetarian_count - other_vegetarian_count
    if red_meat_vegetarian_count > min(red_meat_slots, len(red_meat_vegetarian)):
        raise ValueError(
            "Not enough vegetarian meals match the criteria within the "
            "maximum red meat meals"
        )

    selected_vegetarian = rng.sample(other_vegetarian, other_vegetarian_count)
    selected_red_meat_vegetarian = rng.sample(
        red_meat_vegetarian, red_meat_vegetarian_count
    )
    selected = selected_vegetarian + selected_red_meat_vegetarian
    selected_names = {meal.name for meal in selected}
    remaining_pool = [meal for meal in pool if meal.name not in selected_names]
    remaining_red_meat = [meal for meal in remaining_pool if _is_red_meat_meal(meal)]
    remaining_other = [meal for meal in remaining_pool if not _is_red_meat_meal(meal)]
    remaining_count = count - vegetarian_count
    available_red_meat_slots = red_meat_slots - red_meat_vegetarian_count
    min_red_meat_needed = max(0, remaining_count - len(remaining_other))
    max_red_meat_allowed = min(available_red_meat_slots, len(remaining_red_meat))
    if min_red_meat_needed > max_red_meat_allowed:
        raise ValueError(
            "Not enough meals match the criteria within the " "maximum red meat meals"
        )

    red_meat_count = rng.randint(min_red_meat_needed, max_red_meat_allowed)
    selected.extend(rng.sample(remaining_red_meat, red_meat_count))
    selected.extend(rng.sample(remaining_other, remaining_count - red_meat_count))
    return selected


def reroll_meal(
    meals: list[Meal],
    config: Config,
    current_selection: list[Meal],
    index: int,
    rng: random.Random | None = None,
) -> list[Meal]:
    """Replace a meal while preserving applicable selection constraints."""
    rng = rng or random.Random()
    pool = filter_meals(meals, config)
    current = current_selection[index]
    if current.name in config.forced_meals:
        raise ValueError("Uncheck this forced meal before re-rolling it")
    other_names = {
        meal.name
        for meal_index, meal in enumerate(current_selection)
        if meal_index != index
    }
    non_current = [meal for meal in pool if meal.name != current.name]
    current_vegetarian_count = sum(meal.vegetarian for meal in current_selection)
    if current_vegetarian_count - int(current.vegetarian) < config.min_vegetarian:
        non_current = [meal for meal in non_current if meal.vegetarian]
    if config.max_red_meat_meals is not None:
        other_red_meat_count = sum(
            _is_red_meat_meal(meal)
            for meal_index, meal in enumerate(current_selection)
            if meal_index != index
        )
        if other_red_meat_count >= config.max_red_meat_meals:
            non_current = [meal for meal in non_current if not _is_red_meat_meal(meal)]
    if not non_current:
        raise ValueError(
            "No alternative meals available for re-roll with the " "current criteria"
        )
    candidates = [meal for meal in non_current if meal.name not in other_names]
    chosen_pool = candidates or non_current

    new_selection = list(current_selection)
    new_selection[index] = rng.choice(chosen_pool)
    return new_selection
