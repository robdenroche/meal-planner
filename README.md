# meal-planner

## Development setup

Backend logic lives in the `mealplanner` package and is developed inside a conda
environment named `meal`.

```bash
conda create -n meal python=3.11 -y
conda activate meal
pip install -e '.[dev]'
```

Run tests with:

```bash
conda run -n meal pytest
```

## Try it out

With the `meal` environment activated (`conda activate meal`), generate a week
of meals from `mains.yaml` and refine it interactively:

```bash
mealplanner --num-meals 4 --exclude-protein seafood --effort weeknight
```

At the prompt, enter a meal's number to re-roll it, or press Enter to lock in
the week and print the combined shopping list. Run `mealplanner --help` for
all the filtering options (protein include/exclude, effort, vegetarian-only,
leftovers-only, a fixed `--seed`, etc.).

Note: use `conda activate meal` rather than `conda run -n meal mealplanner`
for the interactive prompt — `conda run` doesn't forward stdin properly for
interactive input.