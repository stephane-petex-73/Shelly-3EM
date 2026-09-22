#!/usr/bin/env python3
"""Lecture des données d'un Shelly 3EM (Gen1) sur le réseau local."""

from __future__ import annotations

import argparse
import json
from typing import Any

import requests

DEFAULT_IP = "192.168.11.100"
DEFAULT_PORT = 80
TIMEOUT_SECONDS = 5


def fetch_status(ip: str, port: int, timeout: int = TIMEOUT_SECONDS) -> dict[str, Any]:
    """Récupère le statut JSON du Shelly à partir de l'API HTTP."""
    endpoint = f"http://{ip}:{port}/status"
    response = requests.get(endpoint, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"Réponse invalide depuis {endpoint}: {payload!r}")
    return payload


def get_meter_list(status: dict[str, Any]) -> list[dict[str, Any]]:
    """Retourne la liste des compteurs disponibles."""
    if isinstance(status.get("meters"), list):
        return status["meters"]
    if isinstance(status.get("emeters"), list):
        return status["emeters"]
    raise KeyError("Le Shelly ne renvoie pas de données de compteurs (meters/emeters).")


def show_entry_values(meter: dict[str, Any], label: str) -> None:
    power = meter.get("power")
    current = meter.get("current")
    voltage = meter.get("voltage")
    total = meter.get("total")

    print(f"Entrée {label} :")
    print(f"  Puissance active : {power} W")
    print(f"  Courant  : {current} A")
    print(f"  Tension  : {voltage} V")
    print(f"  Total    : {total} Wh")
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lecture des valeurs d'un Shelly 3EM.")
    parser.add_argument("--ip", default=DEFAULT_IP, help="Adresse IP du Shelly 3EM (défaut: 192.168.11.100)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port HTTP du Shelly (défaut: 80)")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_SECONDS, help="Timeout de connexion en secondes")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print(f"Lecture du Shelly 3EM sur http://{args.ip}:{args.port}")

    try:
        status = fetch_status(args.ip, args.port, args.timeout)
        meters = get_meter_list(status)
    except requests.RequestException as exc:
        print(f"Erreur de connexion au Shelly: {exc}")
        raise SystemExit(1)
    except (KeyError, ValueError, TypeError) as exc:
        print(f"Erreur de lecture du statut Shelly: {exc}")
        raise SystemExit(1)

    if len(meters) < 2:
        print("Le Shelly ne renvoie pas assez de compteurs pour afficher les entrées A et B.")
        raise SystemExit(1)

    input_a = meters[0]
    input_b = meters[1]

    show_entry_values(input_a, "A")
    show_entry_values(input_b, "B")


if __name__ == "__main__":
    main()
