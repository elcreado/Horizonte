"""Datos sintéticos reproducibles; ninguna fila representa una empresa real."""

import calendar
import csv
import hashlib
import json
import math
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

PROFILES = ("retail", "services", "seasonal", "declining", "volatile")
CENT = Decimal("0.01")


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(CENT)


def generate_dataset(output: Path, *, seed: int = 20261004, companies: int = 100) -> dict:
    if not 1 <= companies <= 1000:
        raise ValueError("Número de empresas fuera de rango.")
    output.mkdir(parents=True, exist_ok=True)
    daily_path = output / "daily.csv"
    obligations_path = output / "obligations.csv"
    start, end = date(2023, 1, 1), date(2024, 12, 31)
    days = (end - start).days + 1
    deficit_companies = set()
    with (
        daily_path.open("w", newline="", encoding="utf-8") as daily_file,
        obligations_path.open("w", newline="", encoding="utf-8") as obligations_file,
    ):
        daily = csv.DictWriter(
            daily_file,
            fieldnames=[
                "company_id",
                "profile",
                "date",
                "variable_flow",
                "known_flow",
                "balance",
            ],
        )
        obligations = csv.DictWriter(
            obligations_file,
            fieldnames=[
                "company_id",
                "id",
                "announced_on",
                "due_date",
                "amount",
                "kind",
            ],
        )
        daily.writeheader()
        obligations.writeheader()
        for company in range(1, companies + 1):
            rng = random.Random(seed + company * 104729)
            profile = PROFILES[(company - 1) % len(PROFILES)]
            scale = money(rng.uniform(0.7, 2.3))
            balance = money((3000000 if profile == "declining" else 12000000) * scale)
            for offset in range(days):
                day = start + timedelta(days=offset)
                seasonal = 1 + 0.25 * math.sin(2 * math.pi * offset / 365.25)
                trend = 1 - 0.90 * offset / days if profile == "declining" else 1
                weekday = [0.8, 0.9, 1.0, 1.05, 1.3, 1.45, 0.3][day.weekday()]
                baseline = 320000 * weekday
                if profile == "seasonal":
                    baseline *= seasonal
                elif profile == "services":
                    baseline *= 0.25 if day.weekday() >= 5 else 1.5
                noise = rng.gauss(0, 200000 if profile == "volatile" else 35000)
                variable = money((baseline * trend + noise) * float(scale))
                known = Decimal("0.00")
                schedule = []
                if day.day == 1:
                    schedule.append(("rent", money(-1800000 * scale)))
                if day.day == 15:
                    schedule.append(("payroll", money(-3200000 * scale)))
                if day.day == calendar.monthrange(day.year, day.month)[1]:
                    schedule.append(("supplier", money(-1700000 * scale)))
                # Un shock a mitad del segundo año se conoce solo 7 días antes.
                if profile == "volatile" and day == date(2024, 7, 10):
                    schedule.append(("shock", money(-80000000 * scale)))
                for kind, amount in schedule:
                    notice = 7 if kind == "shock" else 30
                    obligations.writerow(
                        {
                            "company_id": company,
                            "id": f"{company}-{day.isoformat()}-{kind}",
                            "announced_on": (day - timedelta(days=notice)).isoformat(),
                            "due_date": day.isoformat(),
                            "amount": str(amount),
                            "kind": kind,
                        }
                    )
                    known += amount
                balance += variable + known
                if balance < 0:
                    deficit_companies.add(company)
                daily.writerow(
                    {
                        "company_id": company,
                        "profile": profile,
                        "date": day.isoformat(),
                        "variable_flow": str(variable),
                        "known_flow": str(known),
                        "balance": str(balance),
                    }
                )
    hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in [daily_path, obligations_path]
    }
    manifest = {
        "generator": "synthetic_v1",
        "seed": seed,
        "companies": companies,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "months": 24,
        "days": days,
        "daily_rows": companies * days,
        "profiles": list(PROFILES),
        "currency": "COP",
        "companies_with_negative_balance": len(deficit_companies),
        "sha256": hashes,
        "assumptions": [
            "Historial diario completo y sin faltantes; no valida cold start ni datos reales.",
            "Flujo residual separado por el generador: extracción perfecta, sin error de clasificación.",
            "Obligaciones solo visibles desde announced_on; no se revelan compromisos futuros antes.",
            "Saldo inicial de 3 millones COP para declining y 12 millones para los demás, por escala.",
            "Dataset controlado para evaluación; no demuestra precisión en microempresas reales.",
        ],
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest
