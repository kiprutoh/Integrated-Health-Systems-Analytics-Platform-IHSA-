"""
Reporting service (charter Phase D).

v0.1.0 ships a working Excel exporter for scenario results. Word/PDF/PowerPoint
exporters are declared with a common interface and completed in later releases
(the maternal-mortality work already established docx/pptx pipelines to reuse).
"""
from __future__ import annotations

import io
from typing import Protocol

import pandas as pd


class Exporter(Protocol):
    def export(self, result_dict: dict) -> bytes: ...


class ExcelExporter:
    """Serialise a ScenarioResult.to_dict() into a multi-sheet workbook."""

    def export(self, result: dict) -> bytes:
        summary = pd.DataFrame([
            {"Field": "Domain", "Value": result["domain"]},
            {"Field": "Country", "Value": result["country"]},
            {"Field": "Baseline year", "Value": result["year"]},
            {"Field": "Primary outcome", "Value": result["primary_outcome"]},
        ])
        po = result["primary_outcome"]
        outcomes = pd.DataFrame([
            {"Outcome": k,
             "Baseline": result["baseline_outcome"].get(k),
             "Scenario": result["scenario_outcome"].get(k),
             "Change %": result["relative_change_pct"].get(k)}
            for k in result["baseline_outcome"]
        ])
        levers = pd.DataFrame([
            {"Lever": k, "Baseline": result["baseline_state"].get(k),
             "Scenario": result["scenario_state"].get(k)}
            for k in result["scenario_state"]
        ])
        sens = pd.DataFrame(result.get("sensitivity", []))
        recs = pd.DataFrame({"Recommendation": result.get("recommendations", [])})
        fc = result.get("forecast", {})
        forecast = pd.DataFrame({"Year": fc.get("years", []),
                                 fc.get("outcome", po): fc.get("values", [])})

        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as xl:
            summary.to_excel(xl, sheet_name="Summary", index=False)
            outcomes.to_excel(xl, sheet_name="Outcomes", index=False)
            levers.to_excel(xl, sheet_name="Levers", index=False)
            if not sens.empty:
                sens.to_excel(xl, sheet_name="Sensitivity", index=False)
            if not forecast.empty:
                forecast.to_excel(xl, sheet_name="Forecast", index=False)
            recs.to_excel(xl, sheet_name="Recommendations", index=False)
        buf.seek(0)
        return buf.getvalue()


class WordExporter:  # pragma: no cover - Phase D
    def export(self, result: dict) -> bytes:
        raise NotImplementedError("Word export lands in a later release (reuse docx pipeline).")


class PDFExporter:  # pragma: no cover - Phase D
    def export(self, result: dict) -> bytes:
        raise NotImplementedError("PDF export lands in a later release.")


class PowerPointExporter:  # pragma: no cover - Phase D
    def export(self, result: dict) -> bytes:
        raise NotImplementedError("PPTX export lands in a later release (reuse pptx pipeline).")


EXPORTERS = {"excel": ExcelExporter, "word": WordExporter,
             "pdf": PDFExporter, "pptx": PowerPointExporter}


def get_exporter(fmt: str) -> Exporter:
    if fmt not in EXPORTERS:
        raise KeyError(f"Unknown format '{fmt}'. Available: {sorted(EXPORTERS)}")
    return EXPORTERS[fmt]()
