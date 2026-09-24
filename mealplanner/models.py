"""Meal data model and YAML loading."""

from __future__ import annotations

from dataclasses import dataclass, field

import yaml


@dataclass
class Meal:
    name: str
    ingredients: list[str] = field(default_factory=list)
    pantry: list[str] = field(default_factory=list)
    effort: str | None = None
    protein: str | None = None
    leftovers: bool = False
    vegetarian: bool = False
    recipe: str | None = None


def load_meals(yaml_text: str) -> list[Meal]:
    """Parse the mains.yaml contents into a list of Meal objects."""
    raw = yaml.safe_load(yaml_text) or {}
    meals: list[Meal] = []
    for name, attrs in raw.items():
        attrs = attrs or {}
        meals.append(
            Meal(
                name=name,
                ingredients=list(attrs.get("ingredients") or []),
                pantry=list(attrs.get("pantry") or []),
                effort=attrs.get("effort"),
                protein=attrs.get("protein"),
                leftovers=bool(attrs.get("leftovers", False)),
                vegetarian=bool(attrs.get("vegetarian", False)),
                recipe=attrs.get("recipe"),
            )
        )
    return meals
