from decimal import Decimal


def render_report(report: dict) -> str:
    manifest = report["dataset"]
    lines = [
        "# Evaluación sintética de caja — corte reproducible",
        "",
        "Generado con `python backend/manage.py research_forecast`. No requiere Docker ni APIs.",
        "",
        f"Dataset: {manifest['companies']} empresas, 24 meses (2023–2024), {manifest['daily_rows']} días-empresa completos.",
        f"Semilla {manifest['seed']}; {manifest['companies_with_negative_balance']} empresas tienen saldo negativo en algún momento.",
        "",
        f"Entrenamiento inicial {report['min_train']} días, expansión temporal y paso de {report['step']} días.",
        "Los flujos conocidos se incorporan solo si su anuncio ya ocurrió al corte.",
        "MAE/RMSE son del saldo diario acumulado en COP. Nuevo déficit excluye cortes ya negativos.",
        "DLDE solo cuando ambos escenarios tienen déficit; las ausencias no se convierten en cero.",
        "",
        "| Horizonte | Método | Ventanas | MAE saldo COP | RMSE saldo COP | Precision | Recall | F1 | DLDE días | Pares DLDE |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def number(value, digits=3):
        return "—" if value is None else f"{Decimal(value):.{digits}f}"

    for row in report["metrics"]:
        lines.append(
            f"| {row['horizon']} | {row['method']} | {row['windows']} | "
            f"{number(row['balance_mae'], 2)} | {number(row['balance_rmse'], 2)} | "
            f"{number(row['precision'])} | {number(row['recall'])} | {number(row['f1'])} | "
            f"{number(row['dlde_mean_days'])} | {row['dlde_pairs']} |"
        )
    lines.extend(
        [
            "",
            "## Límites y pendientes",
            "",
            *["- " + item for item in manifest["assumptions"]],
            *["- " + item for item in report["limitations"]],
            "- Perfiles y shocks diseñados para incluir crisis; no representan su frecuencia real.",
            "- Compromisos mensuales anunciados 30 días antes y shock 7 días antes; hybrid_weekly extrapola patrones desde el pasado y no predice shocks nuevos.",
            "- No se conectan estas métricas retrospectivas a una etiqueta de confianza en la interfaz.",
            "- Faltan comparación ARIMA/Prophet, intervalos calibrados, corpus independiente y usabilidad.",
            "",
            "## Integridad",
            "",
            *[f"- `{name}`: SHA-256 `{digest}`" for name, digest in manifest["sha256"].items()],
            "",
            "Datos y métricas sin redondear: `data/generated/manifest.json`, `daily.csv`, `obligations.csv` y `evaluation.json`.",
            "Reproducir con la misma semilla y parámetros; se rechazan archivos cuyo checksum cambió.",
            "Los CSV se regeneran y están ignorados por Git; este informe queda versionado.",
        ]
    )
    return "\n".join(lines) + "\n"
