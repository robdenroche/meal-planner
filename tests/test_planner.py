import random

import pytest

from mealplanner.models import load_meals
from mealplanner.planner import Config, filter_meals, reroll_meal, select_week

from .fixtures import SAMPLE_YAML


@pytest.fixture
def meals():
    return load_meals(SAMPLE_YAML)


def test_filter_meals_vegetarian_only(meals):
    result = filter_meals(meals, Config(vegetarian_only=True))
    assert [m.name for m in result] == ["Veggie Bowl"]


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
