"""Lightweight self-test (runs the core suite without pytest)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from warehouse import reference
from scenario_engine import ScenarioEngine, list_models, load_builtin_models
from forecasting.base import approach_to_target
from etl import get_client

load_builtin_models()
checks = []

def ok(name, cond):
    checks.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name)

ok("47 AFRO countries", len(reference.countries()) == 47)
ok("unique iso3", reference.countries()["iso3"].nunique() == 47)
ok("iso3 lookup Kenya=KEN", reference.iso3_of("Kenya") == "KEN")
ok("domains registered", {"hiv","maternal"} <= set(list_models()))

eng = ScenarioEngine(domain="hiv")
r0 = eng.run("Kenya", {})
ok("hiv baseline invariance", abs(r0.baseline_outcome["hiv_incidence"]-r0.scenario_outcome["hiv_incidence"]) < 1e-6)
r = eng.run("Kenya", {"viral_suppression":95,"condom_use":80,"vmmc_coverage":90})
ok("hiv package reduces incidence", r.relative_change_pct["hiv_incidence"] < 0)
ok("sensitivity non-empty", len(r.sensitivity) > 0)

em = ScenarioEngine(domain="maternal").run("Nigeria", {"sba":90})
ok("maternal via same engine", em.relative_change_pct["mmr"] < 0)

p = approach_to_target(10,2,2023,horizon=6)
ok("forecast converges", abs(p.values[-1]-2) < abs(p.values[0]-2))

c = get_client("worldbank")
rows = c.parse([{"pages":1},[{"countryiso3code":"KEN","date":"2019","value":1800.0,"indicator":{"id":"NY.GDP.PCAP.CD"}}]])
ok("worldbank parse", rows and rows[0]["iso3"]=="KEN")
ok("validate drops nulls", len(c.validate([{"value":1},{"value":None}]))==1)

passed = sum(1 for _,c_ in checks if c_)
print(f"\n{passed}/{len(checks)} checks passed")
sys.exit(0 if passed==len(checks) else 1)
