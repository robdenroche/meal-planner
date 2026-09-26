// Front-end for the meal planner, running the mealplanner Python package in-browser via Pyodide.

const MEALPLANNER_FILES = ["__init__.py", "models.py", "planner.py", "shopping_list.py"];

const statusEl = document.getElementById("status");
const configView = document.getElementById("config-view");
const weekView = document.getElementById("week-view");
const shoppingView = document.getElementById("shopping-view");

let pyodide;
let pyGenerateWeek;
let pyReroll;
let pyShoppingList;

function showView(view) {
  for (const el of [configView, weekView, shoppingView]) {
    el.hidden = el !== view;
  }
}

async function loadMealplannerIntoPyodide(py) {
  py.FS.mkdirTree("/home/pyodide/mealplanner");
  for (const filename of MEALPLANNER_FILES) {
    const response = await fetch(`mealplanner/${filename}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch mealplanner/${filename}: ${response.status}`);
    }
    const text = await response.text();
    py.FS.writeFile(`/home/pyodide/mealplanner/${filename}`, text);
  }

  const mainsResponse = await fetch("mains.yaml");
  if (!mainsResponse.ok) {
    throw new Error(`Failed to fetch mains.yaml: ${mainsResponse.status}`);
  }
  const mainsYamlText = await mainsResponse.text();
  py.globals.set("mains_yaml_text", mainsYamlText);

  await py.runPythonAsync(`
import sys
import random
import json

sys.path.insert(0, "/home/pyodide")

from mealplanner.models import load_meals
from mealplanner.planner import Config, select_week, reroll_meal
from mealplanner.shopping_list import build_grouped_shopping_list

meals = load_meals(mains_yaml_text)
_selection = []


def _meal_to_dict(m):
    return {
        "name": m.name,
        "ingredients": m.ingredients,
        "pantry": m.pantry,
        "effort": m.effort,
        "protein": m.protein,
        "leftovers": m.leftovers,
        "vegetarian": m.vegetarian,
        "recipe": m.recipe,
    }


def _config_from_json(config_json):
    d = json.loads(config_json)
    return Config(
        num_meals=d.get("num_meals", 5),
        include_proteins=set(d["include_proteins"]) if d.get("include_proteins") else None,
        exclude_proteins=set(d.get("exclude_proteins") or []),
        efforts=set(d["efforts"]) if d.get("efforts") else None,
        min_vegetarian=d.get("min_vegetarian", 0),
        leftovers_only=bool(d.get("leftovers_only")),
        forced_meals=set(d.get("forced_meals") or []),
        max_red_meat_meals=(
          int(d["max_red_meat_meals"])
          if d.get("max_red_meat_meals") is not None
          else None
        ),
    )


def available_options():
    return json.dumps(
        {
            "efforts": sorted({m.effort for m in meals if m.effort}),
            "proteins": sorted({m.protein for m in meals if m.protein}),
          "meals": [{"name": m.name, "recipe": m.recipe} for m in meals],
        }
    )


def generate_week(config_json):
    global _selection
    config = _config_from_json(config_json)
    _selection = select_week(meals, config, rng=random.Random())
    return json.dumps([_meal_to_dict(m) for m in _selection])


def reroll(config_json, index):
    global _selection
    config = _config_from_json(config_json)
    _selection = reroll_meal(meals, config, _selection, index=index, rng=random.Random())
    return json.dumps([_meal_to_dict(m) for m in _selection])


def shopping_list_json():
    return json.dumps(build_grouped_shopping_list(_selection))
`);
}

function buildCheckboxGroup(fieldset, name, values) {
  fieldset.querySelectorAll("label").forEach((el) => el.remove());
  for (const value of values) {
    const label = document.createElement("label");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.name = name;
    input.value = value;
    label.appendChild(input);
    label.append(` ${value}`);
    fieldset.appendChild(label);
  }
}

function buildForcedMealList(container, meals) {
  container.replaceChildren();
  const sortedMeals = [...meals].sort((first, second) =>
    first.name.localeCompare(second.name, undefined, { sensitivity: "base" }),
  );
  for (const meal of sortedMeals) {
    const label = document.createElement("label");
    label.className = "forced-meal-option";

    const input = document.createElement("input");
    input.type = "checkbox";
    input.name = "forced-meal";
    input.value = meal.name;
    label.appendChild(input);

    if (meal.recipe) {
      const link = document.createElement("a");
      link.href = meal.recipe;
      link.target = "_blank";
      link.rel = "noopener";
      link.textContent = meal.name;
      label.appendChild(link);
    } else {
      label.append(meal.name);
    }

    container.appendChild(label);
  }
}

function checkedValues(name) {
  return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`)).map((el) => el.value);
}

function readConfigFromForm() {
  const maxRedMeatMeals = document.getElementById("max-red-meat-meals").value;
  return {
    num_meals: Number(document.getElementById("num-meals").value),
    efforts: checkedValues("effort").length ? checkedValues("effort") : null,
    include_proteins: checkedValues("include-protein").length ? checkedValues("include-protein") : null,
    exclude_proteins: checkedValues("exclude-protein"),
    min_vegetarian: Number(document.getElementById("min-vegetarian").value),
    leftovers_only: document.getElementById("leftovers-only").checked,
    forced_meals: checkedValues("forced-meal"),
    max_red_meat_meals:
      maxRedMeatMeals === "" ? null : Number(maxRedMeatMeals),
  };
}

function renderMealCard(meal, index) {
  const li = document.createElement("li");
  li.className = "meal-card";

  const tags = [meal.effort, meal.protein];
  if (meal.vegetarian) tags.push("vegetarian");
  if (meal.leftovers) tags.push("leftovers");

  const recipeLink = meal.recipe
    ? `<p><a href="${meal.recipe}" target="_blank" rel="noopener">Recipe</a></p>`
    : "";

  li.innerHTML = `
    <h3>${meal.name}</h3>
    <div class="tags">${tags.filter(Boolean).join(", ")}</div>
    <div class="ingredients">${meal.ingredients.join(", ")}</div>
    ${recipeLink}
    <button type="button" data-index="${index}">Reroll</button>
  `;
  const rerollButton = li.querySelector("button");
  if (checkedValues("forced-meal").includes(meal.name)) {
    rerollButton.disabled = true;
    rerollButton.title = "Uncheck this meal to allow re-rolling it";
  }
  rerollButton.addEventListener("click", () => handleReroll(index));
  return li;
}

function renderWeek(meals) {
  const list = document.getElementById("meal-list");
  list.innerHTML = "";
  meals.forEach((meal, index) => list.appendChild(renderMealCard(meal, index)));
}

async function handleGenerate(event) {
  event.preventDefault();
  const errorEl = document.getElementById("config-error");
  errorEl.textContent = "";
  try {
    const meals = JSON.parse(pyGenerateWeek(JSON.stringify(readConfigFromForm())));
    renderWeek(meals);
    document.getElementById("week-error").textContent = "";
    showView(weekView);
  } catch (err) {
    errorEl.textContent = pythonErrorMessage(err);
  }
}

async function handleReroll(index) {
  const errorEl = document.getElementById("week-error");
  errorEl.textContent = "";
  try {
    const meals = JSON.parse(pyReroll(JSON.stringify(readConfigFromForm()), index));
    renderWeek(meals);
  } catch (err) {
    errorEl.textContent = pythonErrorMessage(err);
  }
}

function renderShoppingList() {
  const sections = JSON.parse(pyShoppingList());
  const container = document.getElementById("shopping-list");
  container.innerHTML = "";
  for (const section of sections) {
    const sectionEl = document.createElement("section");
    sectionEl.className = "shopping-section";

    const heading = document.createElement("h3");
    heading.textContent = section.section;
    sectionEl.appendChild(heading);

    const groups = section.recipes || [{ items: section.items }];
    for (const groupData of groups) {
      const group = document.createElement("div");
      group.className = "shopping-recipe";

      if (groupData.recipe) {
        const recipeHeading = document.createElement("h4");
        if (groupData.recipe_url) {
          const recipeLink = document.createElement("a");
          recipeLink.href = groupData.recipe_url;
          recipeLink.target = "_blank";
          recipeLink.rel = "noopener";
          recipeLink.textContent = groupData.recipe;
          recipeHeading.appendChild(recipeLink);
        } else {
          recipeHeading.textContent = groupData.recipe;
        }
        group.appendChild(recipeHeading);
      }

      const list = document.createElement("ul");
      for (const item of groupData.items) {
        const li = document.createElement("li");
        li.textContent = item;
        list.appendChild(li);
      }
      group.appendChild(list);
      sectionEl.appendChild(group);
    }

    container.appendChild(sectionEl);
  }
}

function pythonErrorMessage(err) {
  // Pyodide wraps Python exceptions; surface just the message the app raised.
  const message = err && err.message ? err.message : String(err);
  const match = message.match(/ValueError: (.+)/);
  return match ? match[1] : message;
}

async function init() {
  pyodide = await loadPyodide();
  await pyodide.loadPackage("pyyaml");
  await loadMealplannerIntoPyodide(pyodide);

  pyGenerateWeek = pyodide.globals.get("generate_week");
  pyReroll = pyodide.globals.get("reroll");
  pyShoppingList = pyodide.globals.get("shopping_list_json");

  const options = JSON.parse(pyodide.globals.get("available_options")());
  buildCheckboxGroup(document.getElementById("effort-fieldset"), "effort", options.efforts);
  buildCheckboxGroup(document.getElementById("include-protein-fieldset"), "include-protein", options.proteins);
  buildCheckboxGroup(document.getElementById("exclude-protein-fieldset"), "exclude-protein", options.proteins);
  buildForcedMealList(document.getElementById("forced-meals-list"), options.meals);

  document.getElementById("config-form").addEventListener("submit", handleGenerate);
  document.getElementById("back-to-config").addEventListener("click", () => showView(configView));
  document.getElementById("lock-in").addEventListener("click", () => {
    renderShoppingList();
    showView(shoppingView);
  });
  document.getElementById("start-over").addEventListener("click", () => showView(configView));

  statusEl.textContent = `Loaded ${pyodide.runPython("len(meals)")} meals.`;
  showView(configView);
}

init().catch((err) => {
  statusEl.textContent = `Failed to start: ${err.message || err}`;
  console.error(err);
});
