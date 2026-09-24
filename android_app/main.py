from __future__ import annotations

from typing import Any

import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

SHELLY_IP = "192.168.11.100"


class ShellyApiClient:
    def __init__(self, ip: str):
        self.ip = ip

    def fetch_status(self) -> dict[str, Any]:
        url = f"http://{self.ip}/status"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Réponse invalide du Shelly")
        return payload


class MeterCard(BoxLayout):
    def __init__(self, title: str, accent: tuple[float, float, float, float], **kwargs):
        super().__init__(orientation="vertical", spacing=4, padding=(12, 10), **kwargs)
        self.size_hint_y = None
        self.height = 170
        self.canvas.before.clear()
        with self.canvas.before:
            Color(1, 1, 1, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
        self.title = Label(
            text=title,
            color=accent,
            bold=True,
            font_size="18sp",
            size_hint_y=None,
            height=28,
            halign="left",
            valign="middle",
            text_size=(self.width, None),
        )
        self.add_widget(self.title)

        self.data_rows = [
            ("Puissance", "-- W"),
            ("Courant", "-- A"),
            ("Tension", "-- V"),
            ("Total", "-- Wh"),
        ]

        for label_name, value in self.data_rows:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=24, spacing=6)
            row.add_widget(Label(text=f"{label_name} :", font_size="13sp", color=(0.2, 0.2, 0.2, 1), halign="left", valign="middle"))
            value_label = Label(text=value, font_size="13sp", color=(0.15, 0.15, 0.15, 1), halign="right", valign="middle")
            row.add_widget(value_label)
            self.add_widget(row)

    def update(self, meter: dict[str, Any] | None) -> None:
        meter = meter or {}
        values = {
            "Puissance": f"{meter.get('power', 'N/A')} W",
            "Courant": f"{meter.get('current', 'N/A')} A",
            "Tension": f"{meter.get('voltage', 'N/A')} V",
            "Total": f"{meter.get('total', 'N/A')} Wh",
        }
        for child in self.children:
            if isinstance(child, BoxLayout) and len(child.children) == 2:
                key_label = child.children[0]
                value_label = child.children[1]
                if hasattr(key_label, "text") and key_label.text.endswith(":"):
                    key_name = key_label.text[:-1].strip()
                    if key_name in values:
                        value_label.text = values[key_name]


class ShellyAndroidApp(App):
    def build(self):
        self.client = ShellyApiClient(SHELLY_IP)
        Window.clearcolor = (0.92, 0.95, 0.98, 1)

        self.root = ScrollView(do_scroll_x=False, do_scroll_y=True)
        self.content = BoxLayout(orientation="vertical", spacing=12, padding=(16, 16), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter("height"))

        title_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=52, spacing=10)
        title_label = Label(text="Shelly 3EM", bold=True, font_size="28sp", color=(0.08, 0.12, 0.18, 1), halign="left")
        version_label = Label(text="Version 3", bold=True, font_size="16sp", color=(0.11, 0.42, 0.82, 1), halign="right")
        title_bar.add_widget(title_label)
        title_bar.add_widget(version_label)
        self.content.add_widget(title_bar)

        toolbar = BoxLayout(orientation="horizontal", size_hint_y=None, height=52, spacing=8)
        self.ip_input = TextInput(text=SHELLY_IP, multiline=False, hint_text="IP Shelly")
        self.ip_input.bind(on_text_validate=self.refresh_data)
        toolbar.add_widget(self.ip_input)
        self.refresh_btn = Button(text="Rafraîchir", size_hint_x=None, width=140, on_press=self.refresh_data)
        toolbar.add_widget(self.refresh_btn)
        self.content.add_widget(toolbar)

        self.status_label = Label(text="Démarrage…", font_size="14sp", color=(0.2, 0.2, 0.2, 1), halign="left")
        self.content.add_widget(self.status_label)

        self.mode_label = Label(text="Mode : --", bold=True, font_size="18sp", color=(0.2, 0.2, 0.2, 1), halign="left")
        self.content.add_widget(self.mode_label)

        self.consumption_box = self.make_summary_card()
        self.content.add_widget(self.consumption_box)

        self.cards = {
            "A": MeterCard("Entrée A - ENEDIS", (0.85, 0.33, 0.05, 1)),
            "B": MeterCard("Entrée B - Production solaire", (0.14, 0.55, 0.3, 1)),
            "C": MeterCard("Entrée C - Consommation cumulus", (0.28, 0.30, 0.84, 1)),
        }
        for card in self.cards.values():
            self.content.add_widget(card)

        self.root.add_widget(self.content)
        Clock.schedule_once(lambda dt: self.refresh_data(None), 0.6)
        return self.root

    def make_summary_card(self):
        card = BoxLayout(orientation="vertical", padding=(14, 12), spacing=8, size_hint_y=None, height=92)
        card.canvas.before.clear()
        with card.canvas.before:
            Color(1, 1, 1, 1)
            RoundedRectangle(pos=card.pos, size=card.size, radius=[14])
        title = Label(text="Consommation maison", font_size="16sp", bold=True, color=(0.2, 0.2, 0.2, 1), halign="left")
        value = Label(text="0 W", font_size="26sp", bold=True, color=(0.12, 0.18, 0.25, 1), halign="left")
        card.add_widget(title)
        card.add_widget(value)
        card.value_label = value
        return card

    def update_energy_mode(self, power_a: float) -> None:
        if power_a > 0:
            self.mode_label.text = "Mode : Soutirage ENEDIS"
            self.mode_label.color = (0.85, 0.33, 0.05, 1)
        elif power_a < 0:
            self.mode_label.text = "Mode : Injection vers ENEDIS"
            self.mode_label.color = (0.14, 0.55, 0.3, 1)
        else:
            self.mode_label.text = "Mode : Équilibre"
            self.mode_label.color = (0.33, 0.33, 0.33, 1)

    def refresh_data(self, instance):
        try:
            self.client.ip = self.ip_input.text.strip() or SHELLY_IP
            data = self.client.fetch_status()
            meters = data.get("meters") or data.get("emeters") or []
            self.status_label.text = "Connexion OK"
            if len(meters) < 3:
                self.status_label.text = "Erreur : 3 entrées non disponibles"
                return

            meter_a = meters[0]
            meter_b = meters[1]
            meter_c = meters[2]

            self.cards["A"].update(meter_a)
            self.cards["B"].update(meter_b)
            self.cards["C"].update(meter_c)

            power_a = float(meter_a.get("power", 0) or 0)
            power_b = float(meter_b.get("power", 0) or 0)
            power_c = float(meter_c.get("power", 0) or 0)
            self.update_energy_mode(power_a)

            total_consumption = power_a + power_b + power_c
            self.consumption_box.value_label.text = f"{total_consumption:.1f} W"
        except requests.RequestException as exc:
            self.status_label.text = f"Erreur réseau : {exc}"
        except (KeyError, ValueError, TypeError) as exc:
            self.status_label.text = f"Erreur : {exc}"


if __name__ == "__main__":
    ShellyAndroidApp().run()
