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
mealplanner --num-meals 4 --exclude-protein seafood --effort weeknight --min-vegetarian 2
```

At the prompt, enter a meal's number to re-roll it, or press Enter to lock in
the week and print the combined shopping list. Run `mealplanner --help` for
all the filtering options (protein include/exclude, effort, `--min-vegetarian`,
leftovers-only, a fixed `--seed`, etc.).

Note: use `conda activate meal` rather than `conda run -n meal mealplanner`
for the interactive prompt — `conda run` doesn't forward stdin properly for
interactive input.

## Web front-end

`index.html` / `styles.css` / `app.js` at the repo root are a static, build-free
front-end that runs the same `mealplanner` package in the browser via
[Pyodide](https://pyodide.org/). It fetches `mealplanner/*.py` and `mains.yaml`
straight from the repo at runtime, so there's nothing to compile or keep in sync.

Preview it locally (must be served over HTTP, not opened as a `file://` URL):

```bash
python -m http.server 8000
```

Then visit http://localhost:8000/.

### Hosting on GitHub Pages

The root `.nojekyll` file is required so GitHub Pages serves Python files with
underscore-prefixed names, such as `mealplanner/__init__.py`.

1. In the repo settings, under **Pages**, set the source to the `main` branch,
   root folder (`/`).
2. Push to `main`. The site will be published at
   `https://<user>.github.io/meal-planner/` and will always reflect the
   latest `mealplanner` code and `mains.yaml` — no separate build/deploy step
   required.