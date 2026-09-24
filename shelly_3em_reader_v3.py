#!/usr/bin/env python3
"""Interface graphique Version 3 pour lire les valeurs d'un Shelly 3EM (Gen1)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import requests
import tkinter as tk
from tkinter import ttk

DEFAULT_IP = "192.168.11.100"
DEFAULT_PORT = 80
TIMEOUT_SECONDS = 5
LOAD_TIMEOUT_SECONDS = 20


def fetch_status(ip: str, port: int, timeout: int = TIMEOUT_SECONDS) -> dict[str, Any]:
    endpoint = f"http://{ip}:{port}/status"
    response = requests.get(endpoint, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"Réponse invalide depuis {endpoint}: {payload!r}")
    return payload


def get_meter_list(status: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(status.get("meters"), list):
        return status["meters"]
    if isinstance(status.get("emeters"), list):
        return status["emeters"]
    raise KeyError("Le Shelly ne renvoie pas de données de compteurs (meters/emeters).")


class Shelly3EMWindowV3:
    def __init__(self, root: tk.Tk, ip: str = DEFAULT_IP, port: int = DEFAULT_PORT, timeout: int = TIMEOUT_SECONDS):
        self.root = root
        self.ip = ip
        self.port = port
        self.timeout = timeout

        self.root.title("Shelly 3EM - Version 3")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = min(620, max(480, int(screen_width * 0.85)))
        window_height = min(560, max(380, int(screen_height * 0.8)))
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.minsize(480, 380)
        self.root.configure(bg="#eaf2f8")

        self.status_var = tk.StringVar(value="Prêt")
        self.mode_var = tk.StringVar(value="Mode : --")
        self.mode_color = tk.StringVar(value="#666666")
        self.refresh_seconds_var = tk.StringVar(value="5")
        self.ip_var = tk.StringVar(value=ip)
        self.refresh_job = None

        self.value_vars: dict[str, dict[str, tk.StringVar]] = {
            "A": {
                "Puissance": tk.StringVar(value="-- W"),
                "Courant": tk.StringVar(value="-- A"),
                "Tension": tk.StringVar(value="-- V"),
                "Total": tk.StringVar(value="-- Wh"),
            },
            "B": {
                "Puissance": tk.StringVar(value="-- W"),
                "Courant": tk.StringVar(value="-- A"),
                "Tension": tk.StringVar(value="-- V"),
                "Total": tk.StringVar(value="-- Wh"),
            },
            "C": {
                "Puissance": tk.StringVar(value="-- W"),
                "Courant": tk.StringVar(value="-- A"),
                "Tension": tk.StringVar(value="-- V"),
                "Total": tk.StringVar(value="-- Wh"),
            },
        }

        main_container = tk.Frame(self.root, bg="#eaf2f8", padx=20, pady=20)
        main_container.pack(fill="both", expand=True)
        main_container.grid_columnconfigure(0, weight=1)

        title = tk.Label(main_container, text="Données Shelly 3EM", font=("Arial", 14, "bold"), bg="#eaf2f8")
        title.grid(row=0, column=0, sticky="w", pady=(0, 10))

        version_label = tk.Label(main_container, text="Version 3", font=("Arial", 10, "bold"), bg="#eaf2f8", fg="#1d4ed8")
        version_label.grid(row=0, column=1, sticky="e", pady=(0, 10), padx=(0, 6))

        mode_frame = tk.Frame(main_container, bg="#ffffff", bd=1, relief="solid")
        mode_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8), padx=0)
        tk.Label(mode_frame, textvariable=self.mode_var, font=("Arial", 10, "bold"), bg="#ffffff", fg="black").pack(anchor="w", padx=12, pady=(8, 2))
        tk.Label(
            mode_frame,
            text="Si la puissance de l’entrée A est positive → Soutirage ENEDIS\nSi la puissance de l’entrée A est négative → Injection vers ENEDIS\nSi elle est nulle → Équilibre",
            font=("Arial", 7),
            bg="#ffffff",
            fg="#555555",
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 8))

        self.house_consumption_var = tk.StringVar(value="0 W")

        consumption_card = tk.Frame(main_container, bg="#ffffff", bd=1, relief="solid")
        consumption_card.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8), padx=0)
        tk.Label(consumption_card, text="Consommation maison", font=("Arial", 9, "bold"), bg="#ffffff").pack(anchor="w", padx=12, pady=(8, 1))
        tk.Label(consumption_card, textvariable=self.house_consumption_var, font=("Arial", 14, "bold"), bg="#ffffff", fg="#1f2937").pack(anchor="w", padx=12, pady=(0, 8))

        for idx, label in enumerate(["A", "B", "C"]):
            frame = tk.Frame(main_container, bg="#ffffff", bd=1, relief="solid")
            frame.grid(row=idx + 3, column=0, columnspan=2, sticky="ew", pady=(0, 10), padx=0)
            frame.grid_columnconfigure(1, weight=1)

            if label == "A":
                header_text = "Entrée A - ENEDIS"
                header_color = "#d35400"
            elif label == "B":
                header_text = "Entrée B - Production solaire"
                header_color = "#2e8b57"
            else:
                header_text = "Entrée C - Consommation cumulus"
                header_color = "#4f46e5"

            header = tk.Label(frame, text=header_text, font=("Arial", 10, "bold"), bg="#ffffff", fg=header_color)
            header.grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 3))

            for row_index, key in enumerate(["Puissance", "Courant", "Tension", "Total"]):
                tk.Label(frame, text=f"{key} :", font=("Arial", 8, "bold"), bg="#ffffff").grid(
                    row=row_index + 1, column=0, sticky="w", padx=(12, 6), pady=0
                )
                value_label = tk.Label(frame, textvariable=self.value_vars[label][key], fg="#1f1f1f", bg="#ffffff", font=("Arial", 8))
                value_label.grid(row=row_index + 1, column=1, sticky="w", pady=0)

        bottom_bar = tk.Frame(self.root, bg="#dfeaf4")
        bottom_bar.pack(side="bottom", fill="x")

        self.status_label = tk.Label(bottom_bar, textvariable=self.status_var, anchor="w", bg="#dfeaf4")
        self.status_label.pack(side="left", padx=20, pady=12)

        settings_frame = tk.Frame(bottom_bar, bg="#dfeaf4")
        settings_frame.pack(side="right", padx=(0, 20), pady=8)

        tk.Label(settings_frame, text="IP Shelly", font=("Arial", 9), bg="#dfeaf4").grid(row=0, column=0, sticky="w")
        ip_entry = tk.Entry(settings_frame, textvariable=self.ip_var, width=15)
        ip_entry.grid(row=0, column=1, padx=(6, 0))
        ip_entry.bind("<Return>", lambda event: self.set_ip_and_refresh())

        tk.Label(settings_frame, text="Rafraîchissement (s)", font=("Arial", 9), bg="#dfeaf4").grid(row=1, column=0, sticky="w", pady=(6, 0))
        refresh_entry = tk.Entry(settings_frame, textvariable=self.refresh_seconds_var, width=5, justify="center")
        refresh_entry.grid(row=1, column=1, padx=(6, 0), pady=(6, 0))
        refresh_entry.bind("<Return>", lambda event: self.apply_refresh_interval())

        tk.Button(settings_frame, text="OK", width=4, command=self.set_ip_and_refresh, bg="#3b82f6", fg="white", relief="flat").grid(row=1, column=2, padx=(6, 0), pady=(6, 0))

        self.root.after(200, self.refresh_data)

    def set_entry_values(self, label: str, meter: dict[str, Any] | None) -> None:
        meter = meter or {}
        values = {
            "Puissance": f"{meter.get('power', 'N/A')} W",
            "Courant": f"{meter.get('current', 'N/A')} A",
            "Tension": f"{meter.get('voltage', 'N/A')} V",
            "Total": f"{meter.get('total', 'N/A')} Wh",
        }
        for key, value in values.items():
            self.value_vars[label][key].set(value)

    def update_energy_mode(self, power_a: float) -> None:
        if power_a > 0:
            self.mode_var.set("Mode : Soutirage ENEDIS")
            self.mode_color.set("#d35400")
        elif power_a < 0:
            self.mode_var.set("Mode : Injection vers ENEDIS")
            self.mode_color.set("#2e8b57")
        else:
            self.mode_var.set("Mode : Équilibre")
            self.mode_color.set("#666666")

    def set_ip_and_refresh(self) -> None:
        new_ip = self.ip_var.get().strip()
        if not new_ip:
            self.status_var.set("Adresse IP invalide")
            self.ip_var.set(self.ip)
            return

        self.ip = new_ip
        self.apply_refresh_interval()
        self.root.after(200, self.refresh_data)

    def schedule_next_refresh(self) -> None:
        try:
            seconds = int(self.refresh_seconds_var.get())
        except ValueError:
            seconds = 5

        if seconds <= 0:
            if self.refresh_job is not None:
                self.root.after_cancel(self.refresh_job)
                self.refresh_job = None
            self.status_var.set("Rafraîchissement désactivé")
            return

        if self.refresh_job is not None:
            self.root.after_cancel(self.refresh_job)
        self.refresh_job = self.root.after(seconds * 1000, self.refresh_data)

    def apply_refresh_interval(self) -> None:
        try:
            seconds = int(self.refresh_seconds_var.get())
        except ValueError:
            self.status_var.set("Valeur invalide : entre 0 et 60 secondes")
            self.refresh_seconds_var.set("5")
            return

        if seconds < 0 or seconds > 60:
            self.status_var.set("Valeur invalide : entre 0 et 60 secondes")
            self.refresh_seconds_var.set("5")
            return

        if seconds == 0:
            if self.refresh_job is not None:
                self.root.after_cancel(self.refresh_job)
                self.refresh_job = None
            self.status_var.set("Rafraîchissement désactivé")
            return

        self.schedule_next_refresh()

    def refresh_data(self) -> None:
        self.status_var.set("Chargement...")
        self.root.update_idletasks()

        try:
            status = fetch_status(self.ip, self.port, LOAD_TIMEOUT_SECONDS)
            meters = get_meter_list(status)
            if len(meters) < 2:
                raise ValueError("Le Shelly ne renvoie pas assez de compteurs pour afficher les entrées A, B et C.")

            meter_a = meters[0] if len(meters) > 0 else {}
            meter_b = meters[1] if len(meters) > 1 else {}
            meter_c = meters[2] if len(meters) > 2 else {}

            self.set_entry_values("A", meter_a)
            self.set_entry_values("B", meter_b)
            self.set_entry_values("C", meter_c)

            power_a = float(meter_a.get("power", 0) or 0)
            power_b = float(meter_b.get("power", 0) or 0)
            power_c = float(meter_c.get("power", 0) or 0)

            self.update_energy_mode(power_a)

            home_consumption_w = power_a + power_b + power_c
            self.house_consumption_var.set(f"{home_consumption_w:.1f} W")

            self.status_var.set(f"Dernière mise à jour : {datetime.now().strftime('%H:%M:%S')}")
        except requests.exceptions.Timeout:
            self.status_var.set("Erreur : chargement des données > 20 secondes, rafraîchissement arrêté")
            if self.refresh_job is not None:
                self.root.after_cancel(self.refresh_job)
                self.refresh_job = None
            return
        except requests.RequestException as exc:
            self.status_var.set(f"Erreur réseau : {exc}")
        except (KeyError, ValueError, TypeError) as exc:
            self.status_var.set(f"Erreur : {exc}")

        self.schedule_next_refresh()


def main() -> None:
    root = tk.Tk()
    app = Shelly3EMWindowV3(root)
    root.mainloop()


if __name__ == "__main__":
    main()
