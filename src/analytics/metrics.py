from datetime import datetime
import json
from pathlib import Path

def compute_total_ingresos(data):
    ingresos = data.get("oIngresos", {})
    return (
        ingresos.get("decRemuBrutaPublico", 0)
        + ingresos.get("decRemuBrutaPrivado", 0)
        + ingresos.get("decOtroIngresoPublico", 0)
        + ingresos.get("decOtroIngresoPrivado", 0)
    )


def compute_alerts(data):
    alerts = []

    if len(data.get("lSentenciaPenal", [])) > 0:
        alerts.append("SENTENCIA_PENAL")

    if len(data.get("lSentenciaObliga", [])) > 0:
        alerts.append("OBLIGACION_JUDICIAL")

    if len(data.get("lRenunciaOP", [])) > 1:
        alerts.append("MULTIPLES_RENUNCIAS_PARTIDARIAS")

    if len(data.get("lCargoPartidario", [])) > 2:
        alerts.append("ALTA_ROTACION_PARTIDARIA")

    return alerts


def compute_career_years(data):
    cargos = data.get("lCargoPartidario", [])
    if not cargos:
        return 0

    years = []
    for c in cargos:
        try:
            years.append(int(c.get("strAnioCargoPartiDesde", 0)))
            years.append(int(c.get("strAnioCargoPartiHasta", 0)))
        except:
            pass

    if not years:
        return 0

    return max(years) - min(years)


def compute_risk_score(data):
    score = 0

    # Income factor (low income vs political position could be risk signal depending model)
    income = compute_total_ingresos(data)
    if income == 0:
        score += 0.2

    # Legal risk
    if data.get("lSentenciaPenal"):
        score += 0.5

    if data.get("lSentenciaObliga"):
        score += 0.3

    # Party instability
    if len(data.get("lRenunciaOP", [])) > 1:
        score += 0.2

    # Experience stability reduces risk
    years = compute_career_years(data)
    if years > 5:
        score -= 0.2

    return max(0, min(1, score))


def build_metrics(data):
    return {
        "total_ingresos": compute_total_ingresos(data),
        "years_experience": compute_career_years(data),
        "score_riesgo": compute_risk_score(data),
        "lista_alertas": compute_alerts(data),
    }

def main():

    BASE_DIR = Path(__file__).resolve().parents[2]
    json_path = BASE_DIR / "data" / "raw" / "diputados" / "00003467.json"

    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    data = raw["data"]  # important: your JSON is nested

    metrics = build_metrics(data)

    print(metrics)


main()