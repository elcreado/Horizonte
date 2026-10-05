"""Supervisor del servicio gratuito: web y cola en procesos independientes."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def supervise(commands, root):
    """Detiene ambos hijos si alguno termina o si llega una señal de apagado."""
    processes = []
    stopping = False

    def stop(*unused):
        nonlocal stopping
        stopping = True
        for process in processes:
            if process.poll() is None:
                process.terminate()

    previous_handlers = {
        number: signal.signal(number, stop) for number in (signal.SIGTERM, signal.SIGINT)
    }
    try:
        for command in commands:
            if stopping:
                break
            processes.append(subprocess.Popen(command, cwd=root))
        while not stopping and all(process.poll() is None for process in processes):
            time.sleep(1)
    finally:
        unexpected = not stopping
        stop()
        try:
            for process in processes:
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        finally:
            for number, handler in previous_handlers.items():
                signal.signal(number, handler)
    return 1 if unexpected else 0


def main():
    root = Path(__file__).resolve().parent.parent
    subprocess.run([sys.executable, "backend/manage.py", "initialize_schema"], cwd=root, check=True)
    subprocess.run(
        [sys.executable, "backend/manage.py", "migrate", "--noinput"], cwd=root, check=True
    )
    commands = [
        [
            sys.executable,
            "-m",
            "gunicorn",
            "--chdir",
            "backend",
            "config.wsgi:application",
            "--bind",
            "0.0.0.0:" + os.environ.get("PORT", "8000"),
            "--workers",
            "1",
            "--threads",
            "2",
        ],
        [sys.executable, "backend/manage.py", "run_background"],
    ]
    return supervise(commands, root)


if __name__ == "__main__":
    raise SystemExit(main())
