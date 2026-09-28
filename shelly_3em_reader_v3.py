#!/usr/bin/env python3
"""Interface graphique Version 3 pour lire les valeurs d'un Shelly 3EM (Gen1)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import requests
import tkinter as tk
from tkinter import ttk

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
except ImportError:  # pragma: no cover - matplotlib may be absent until installation.
    FigureCanvasTkAgg = None
    Figure = None

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


def append_power_history(history: dict[str, list[float]], values: dict[str, float], limit: int = 120) -> dict[str, list[float]]:
    for name, value in values.items():
        series = history.setdefault(name, [])
        series.append(float(value))
        if len(series) > limit:
            series.pop(0)
    return history


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
        self.history: dict[str, list[float]] = {"A": [], "B": [], "C": [], "Maison": []}
        self.history_times: dict[str, list[datetime]] = {"A": [], "B": [], "C": [], "Maison": []}
        self.max_history_points = 5760
        self.launch_time = datetime.now()

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

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.main_tab = tk.Frame(self.notebook, bg="#eaf2f8")
        self.notebook.add(self.main_tab, text="Mesures")

        main_container = tk.Frame(self.main_tab, bg="#eaf2f8", padx=20, pady=20)
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

        self.graph_tab = tk.Frame(self.notebook, bg="#eaf2f8")
        self.notebook.add(self.graph_tab, text="Graphique")
        if Figure is not None and FigureCanvasTkAgg is not None:
            self.graph_figure = Figure(figsize=(8, 4.5), dpi=100, facecolor="#f4f7fb")
            self.graph_ax = self.graph_figure.add_subplot(111)
            self.graph_canvas = FigureCanvasTkAgg(self.graph_figure, self.graph_tab)
            self.graph_canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=(12, 12))
            self.update_graph()
        else:
            tk.Label(
                self.graph_tab,
                text="Matplotlib n’est pas installé.\nInstallez le paquet matplotlib pour afficher le graphe.",
                bg="#eaf2f8",
                fg="#333333",
                justify="left",
                font=("Arial", 10),
            ).pack(anchor="center", expand=True, padx=20, pady=20)

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

    def update_graph(self) -> None:
        if Figure is None or FigureCanvasTkAgg is None or not hasattr(self, "graph_ax"):
            return

        now = datetime.now()
        start_time = self.launch_time

        self.graph_ax.clear()
        self.graph_ax.set_title("Historique depuis le lancement")
        self.graph_ax.set_xlabel("Temps depuis le lancement")
        self.graph_ax.set_ylabel("Puissance (W)")
        self.graph_ax.grid(True, alpha=0.3)

        colors = {
            "A": "#0b19db",
            "B": "#df6616",
            "C": "#2ce714",
            "Maison": "#d81d1d",
        }
        labels = {
            "A": "Enedis",
            "B": "Production solaire",
            "C": "Cumulus",
            "Maison": "TOTAL conso Maison",
        }
        plotted = False
        all_minutes: list[float] = []

        for key, color in colors.items():
            timestamps = self.history_times.get(key, [])
            values = self.history.get(key, [])
            if not timestamps or not values:
                continue
            filtered = [(ts, value) for ts, value in zip(timestamps, values) if ts >= start_time]
            if not filtered:
                continue
            filtered.sort(key=lambda item: item[0])
            minute_values = [(ts - start_time).total_seconds() / 60.0 for ts, _ in filtered]
            y_values = [value for _, value in filtered]
            all_minutes.extend(minute_values)

            if key == "A":
                segment_points: list[tuple[float, float]] = []
                segment_negative = None
                label_added = False

                for minute, value in zip(minute_values, y_values):
                    current_negative = value < 0
                    if not segment_points:
                        segment_negative = current_negative
                        segment_points.append((minute, value))
                        continue

                    if current_negative != segment_negative:
                        self.graph_ax.plot(
                            [point[0] for point in segment_points],
                            [point[1] for point in segment_points],
                            label=labels[key] if not label_added else None,
                            color=color,
                            linewidth=2,
                            linestyle="--" if segment_negative else "-",
                        )
                        label_added = True
                        segment_points = [(minute, value)]
                        segment_negative = current_negative
                    else:
                        segment_points.append((minute, value))

                if segment_points:
                    self.graph_ax.plot(
                        [point[0] for point in segment_points],
                        [point[1] for point in segment_points],
                        label=labels[key] if not label_added else None,
                        color=color,
                        linewidth=2,
                        linestyle="--" if segment_negative else "-",
                    )
            else:
                self.graph_ax.plot(minute_values, y_values, label=labels[key], color=color, linewidth=2)
            plotted = True

        if all_minutes:
            min_value = 0.0
            max_value = max(all_minutes)
            if max_value == 0:
                max_value = 60
            self.graph_ax.set_xlim(min_value, max_value)
            tick_minutes = list(range(0, int(max_value) + 1, 60))
            if tick_minutes:
                tick_labels = [(start_time + timedelta(minutes=offset)).strftime("%H:%M") for offset in tick_minutes]
                self.graph_ax.set_xticks(tick_minutes)
                self.graph_ax.set_xticklabels(tick_labels, rotation=30)
            self.graph_ax.axhline(0, color="#302E2E", linewidth=1.0, alpha=1.0, linestyle="-")

        if plotted:
            self.graph_ax.legend(loc="upper right")
        self.graph_figure.tight_layout()
        self.graph_canvas.draw_idle()

    def append_history(self, power_a: float, power_b: float, power_c: float) -> None:
        now = datetime.now()
        values = {
            "A": power_a,
            "B": power_b,
            "C": power_c,
            "Maison": power_a + power_b,
        }
        for key, value in values.items():
            series = self.history.setdefault(key, [])
            series.append(float(value))
            self.history_times.setdefault(key, []).append(now)
            if len(series) > self.max_history_points:
                series.pop(0)
                self.history_times[key].pop(0)
        self.update_graph()

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

            home_consumption_w = power_a + power_b
            self.house_consumption_var.set(f"{home_consumption_w:.1f} W")
            self.append_history(power_a, power_b, power_c)

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
