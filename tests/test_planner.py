import random

import pytest

from mealplanner.models import load_meals
from mealplanner.planner import Config, filter_meals, reroll_meal, select_week

from .fixtures import SAMPLE_YAML


@pytest.fixture
def meals():
    return load_meals(SAMPLE_YAML)


def test_select_week_respects_min_vegetarian(meals):
    selection = select_week(
        meals, Config(num_meals=2, min_vegetarian=1), rng=random.Random(0)
    )
    assert any(m.vegetarian for m in selection)


def test_select_week_raises_when_not_enough_vegetarian(meals):
    with pytest.raises(ValueError):
        select_week(meals, Config(num_meals=2, min_vegetarian=2), rng=random.Random(0))


def test_filter_meals_exclude_proteins(meals):
    result = filter_meals(meals, Config(exclude_proteins={"legume"}))
    assert [m.name for m in result] == ["Tacos"]


def test_select_week_returns_requested_count(meals):
    selection = select_week(meals, Config(num_meals=2), rng=random.Random(0))
    assert len(selection) == 2
    assert {m.name for m in selection} == {"Tacos", "Veggie Bowl"}


def test_select_week_raises_when_pool_too_small(meals):
    with pytest.raises(ValueError):
        select_week(meals, Config(num_meals=5), rng=random.Random(0))


def test_reroll_meal_picks_a_different_meal(meals):
    selection = [meals[0], meals[1]]
    rerolled = reroll_meal(
        meals, Config(num_meals=2), selection, index=0, rng=random.Random(1)
    )
    # Only two meals total match the (unfiltered) criteria, so index 0 must become "the other one"
    assert rerolled[0].name != selection[0].name
    assert rerolled[1].name == selection[1].name


def test_reroll_meal_raises_when_no_alternatives(meals):
    single = [meals[0]]
    with pytest.raises(ValueError):
        reroll_meal(
            meals,
            Config(num_meals=1, include_proteins={"beef/poultry"}),
            single,
            index=0,
            rng=random.Random(0),
        )


def test_reroll_meal_keeps_min_vegetarian_when_at_the_minimum(meals):
    # meals[1] ("Veggie Bowl") is the only vegetarian meal in the fixture, so
    # rerolling it while min_vegetarian=1 has no legal alternative.
    selection = [meals[0], meals[1]]
    with pytest.raises(ValueError):
        reroll_meal(
            meals,
            Config(num_meals=2, min_vegetarian=1),
            selection,
            index=1,
            rng=random.Random(0),
        )


def test_reroll_meal_picks_another_vegetarian_meal_to_keep_minimum():
    extra_yaml = SAMPLE_YAML + """
Veggie Chili:
  ingredients:
    - beans
    - tomatoes
    - onion
  effort: weeknight
  protein: legume
  leftovers: TRUE
  vegetarian: TRUE
"""
    meals = load_meals(extra_yaml)
    tacos, veggie_bowl, veggie_chili = meals
    selection = [tacos, veggie_bowl]
    rerolled = reroll_meal(
        meals,
        Config(num_meals=2, min_vegetarian=1),
        selection,
        index=1,
        rng=random.Random(0),
    )
    assert rerolled[1].name == "Veggie Chili"
