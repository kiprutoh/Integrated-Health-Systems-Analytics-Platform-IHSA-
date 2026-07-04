# Adding a domain module

1. Create `analytics/<domain>/model.py` implementing `ScenarioModel`:
   - `domain`, `title`, `primary_outcome`
   - `levers` (list of `LeverSpec`) and `outcomes` (list of `OutcomeSpec`)
   - `countries()`, `baseline(country)`, `simulate(state)` (and optionally `apply`)
2. Register it in `analytics/<domain>/__init__.py`:
   ```python
   from analytics.<domain>.model import MyModel
   from scenario_engine.registry import register_model
   model = register_model(MyModel())
   ```
3. Add the domain to `load_builtin_models()` in `scenario_engine/registry.py`.
4. Add data under `data/processed/<domain>/` and tests under `tests/`.

The UI and API require no changes — they are registry-driven.
