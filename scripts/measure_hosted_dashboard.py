"""Ensayo acotado HTTP de lectura; no mide renderizado ni carga concurrente."""

import argparse
import http.cookiejar
import json
import math
import statistics
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=10)
    args = parser.parse_args()
    if not 5 <= args.samples <= 30:
        parser.error("Usa entre 5 y 30 muestras por horizonte.")
    root = Path(__file__).resolve().parents[1]
    private = root / ".local-logs"
    account = json.loads((private / "remote-qa-account.json").read_text(encoding="utf-8-sig"))
    origin = "https://horizonte-demo.onrender.com"
    company = int(account["company_id"])
    opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def request(path, body=None):
        headers = {"Accept": "application/json"}
        payload = None
        if body is not None:
            with opener.open(origin + "/api/auth/csrf/", timeout=60) as response:
                token = json.load(response)["csrfToken"]
            headers.update(
                {"Content-Type": "application/json", "X-CSRFToken": token, "Origin": origin}
            )
            payload = json.dumps(body).encode()
        started = time.perf_counter()
        try:
            with opener.open(
                Request(origin + path, data=payload, headers=headers), timeout=60
            ) as response:
                response.read()
                status = response.status
        except HTTPError as error:
            status = error.code
            error.close()
        return status, time.perf_counter() - started

    logged_in = False
    try:
        status, _ = request(
            "/api/auth/login/", {"username": account["username"], "password": account["password"]}
        )
        if status != 200:
            raise RuntimeError(f"Inicio de sesión rechazado: HTTP {status}.")
        logged_in = True
        results = []
        for horizon in (30, 60, 90):
            route = f"/api/companies/{company}/dashboard/?horizon={horizon}"
            warm_status, warm_seconds = request(route)
            if warm_status != 200:
                raise RuntimeError(f"Dashboard rechazado: HTTP {warm_status}.")
            times = []
            for _ in range(args.samples):
                status, seconds = request(route)
                if status != 200:
                    raise RuntimeError(f"Muestra rechazada: HTTP {status}.")
                times.append(seconds)
            ordered = sorted(times)
            results.append(
                {
                    "horizon": horizon,
                    "samples": args.samples,
                    "warmup_seconds": warm_seconds,
                    "median_seconds": statistics.median(times),
                    "p95_seconds": ordered[math.ceil(len(times) * 0.95) - 1],
                    "maximum_seconds": max(times),
                    "samples_seconds": times,
                }
            )
        report = {
            "scope": "Sequential warm HTTP reads; no browser rendering or concurrency",
            "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "origin": origin,
            "results": results,
        }
        destination = private / "dashboard-http-timing.json"
        destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {
                    "results": [
                        {key: value for key, value in row.items() if key != "samples_seconds"}
                        for row in results
                    ]
                },
                indent=2,
            )
        )
    finally:
        if logged_in:
            status, _ = request("/api/auth/logout/", {})
            if status != 200:
                raise RuntimeError(f"Cierre de sesión rechazado: HTTP {status}.")


if __name__ == "__main__":
    main()
