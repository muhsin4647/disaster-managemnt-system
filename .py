import tkinter as tk
from tkinter import ttk, messagebox
import random
import threading
import time
import folium
import webbrowser
import requests
from datetime import datetime

API_KEY = "YOUR_API_KEY"  # replace with your OpenWeatherMap key

class DisasterResponseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🌍 Disaster Early Warning System")
        self.root.geometry("820x620")
        self.root.configure(bg="#2b2b2b")

        self.locations = {
            "Kochi": {"coords": [9.9312, 76.2673], "flood_risk": 0.7, "quake_risk": 0.2},
            "Trivandrum": {"coords": [8.5241, 76.9366], "flood_risk": 0.6, "quake_risk": 0.1},
            "Chennai": {"coords": [13.0827, 80.2707], "flood_risk": 0.5, "quake_risk": 0.3},
            "Mumbai": {"coords": [19.0760, 72.8777], "flood_risk": 0.8, "quake_risk": 0.4},
            "Bengaluru": {"coords": [12.9716, 77.5946], "flood_risk": 0.3, "quake_risk": 0.1}
        }
        self.current_location = "Kochi"
        self.weather_data = {"temp": "-", "humidity": "-", "conditions": "-", "rain": 0}
        self.sensor_data = {
            "Flood": {"status": "Normal", "water_level": 0},
            "Earthquake": {"status": "Normal", "seismic_activity": 0}
        }

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#2b2b2b", foreground="#ffffff", font=("Segoe UI", 10))
        style.configure("TLabelframe", background="#2b2b2b", foreground="#ffffff", font=("Segoe UI", 11, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=5)

        self.create_widgets()

        threading.Thread(target=self._weather_loop, daemon=True).start()
        threading.Thread(target=self._sensor_loop, daemon=True).start()

        self.fetch_weather_once()
        self.create_map()

    def create_widgets(self):
        lf_loc = ttk.LabelFrame(self.root, text="🌐 Select Location")
        lf_loc.place(x=10, y=10, width=390, height=60)
        self.location_var = tk.StringVar(self.root, value=self.current_location)
        cb = ttk.Combobox(lf_loc, textvariable=self.location_var,
                          values=list(self.locations), state="readonly")
        cb.pack(padx=5, pady=5, fill="x")
        cb.bind("<<ComboboxSelected>>", lambda e: self.on_location_change())

        lf_w = ttk.LabelFrame(self.root, text="🌡️ Weather")
        lf_w.place(x=410, y=10, width=390, height=150)
        self.weather_labels = {}
        for i, key in enumerate(("temp", "humidity", "conditions", "rain")):
            lbl = ttk.Label(lf_w, text=f"{key.title()}: -")
            lbl.place(x=10, y=5 + i*25)
            self.weather_labels[key] = lbl
        self.current_temp_lbl = ttk.Label(lf_w, text="Current Temperature: -")
        self.current_temp_lbl.place(x=10, y=125)

        lf_p = ttk.LabelFrame(self.root, text="⚠️ Disaster Probabilities")
        lf_p.place(x=10, y=80, width=390, height=100)
        self.prob_labels = {}
        for i, key in enumerate(("flood", "earthquake")):
            lbl = ttk.Label(lf_p, text=f"{key.title()} Risk: -")
            lbl.place(x=10, y=5 + i*30)
            self.prob_labels[key] = lbl

        lf_s = ttk.LabelFrame(self.root, text="📟 Sensors")
        lf_s.place(x=410, y=170, width=390, height=80)
        self.flood_status_lbl = ttk.Label(lf_s, text="Flood: Normal", foreground="green")
        self.flood_status_lbl.place(x=10, y=5)
        self.quake_status_lbl = ttk.Label(lf_s, text="Quake: Normal", foreground="green")
        self.quake_status_lbl.place(x=10, y=35)

        lf_a = ttk.LabelFrame(self.root, text="🚨 Alerts")
        lf_a.place(x=10, y=190, width=790, height=180)
        self.alert_list = tk.Listbox(lf_a, font=("Consolas", 10), bg="#2b2b2b", fg="#ffffff")
        self.alert_list.pack(fill="both", expand=True, padx=5, pady=5)

        btn_update = ttk.Button(self.root, text="📍 Update Map", command=self.create_map)
        btn_update.place(x=200, y=385, width=140)
        btn_drones = ttk.Button(self.root, text="🚁 Dispatch Drones", command=self.dispatch_drones)
        btn_drones.place(x=400, y=385, width=160)

    def on_location_change(self):
        self.current_location = self.location_var.get()
        self.fetch_weather_once()
        self.create_map()
        self.add_alert(f"Location changed to {self.current_location}")

    def fetch_weather_once(self):
        try:
            lat, lon = self.locations[self.current_location]["coords"]
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
            data = requests.get(url).json()
            self.weather_data.update({
                "temp": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "conditions": data["weather"][0]["description"].capitalize(),
                "rain": data.get("rain", {}).get("1h", 0)
            })
            self._update_weather_labels()
            self._update_probabilities()
            self.current_temp_lbl.config(text=f"Current Temperature: {self.weather_data['temp']}°C")
        except Exception as e:
            print("Weather fetch error:", e)

    def _weather_loop(self):
        while True:
            self.fetch_weather_once()
            time.sleep(1800)

    def _sensor_loop(self):
        while True:
            rain = self.weather_data.get("rain", 0)
            wl = rain * 5 + random.randint(0, 100)
            self.sensor_data["Flood"].update({"water_level": wl,
                                              "status": "DANGER" if wl > 200 else "Normal"})
            se = random.uniform(0, 6.0)
            self.sensor_data["Earthquake"].update({"seismic_activity": se,
                                                   "status": "DANGER" if se > 4.5 else "Normal"})
            self.root.after(0, self._update_sensor_labels)
            self.root.after(0, self._check_alerts)
            time.sleep(5)

    def _update_weather_labels(self):
        self.weather_labels["temp"].config(text=f"Temp: {self.weather_data['temp']}°C")
        self.weather_labels["humidity"].config(text=f"Humidity: {self.weather_data['humidity']}%")
        self.weather_labels["conditions"].config(text=f"Conditions: {self.weather_data['conditions']}")
        r = self.weather_data["rain"]
        self.weather_labels["rain"].config(text=f"Rain (1h): {r} mm" if r else "Rain (1h): None")

    def _update_probabilities(self):
        lr = self.locations[self.current_location]
        rain = self.weather_data.get("rain", 0)
        wl = self.sensor_data["Flood"]["water_level"]
        flood_prob = (lr["flood_risk"]*0.6 + rain/50*0.4 + wl/300*0.3) * 100
        quake_prob = (lr["quake_risk"]*0.7 + self.sensor_data["Earthquake"]["seismic_activity"]/6*0.5) * 100

        self.prob_labels["flood"].config(
            text=f"Flood Risk: {min(flood_prob,100):.1f}%",
            foreground="red" if flood_prob>50 else "orange" if flood_prob>30 else "green"
        )
        self.prob_labels["earthquake"].config(
            text=f"Earthquake Risk: {min(quake_prob,100):.1f}%",
            foreground="red" if quake_prob>40 else "orange" if quake_prob>20 else "green"
        )

    def _update_sensor_labels(self):
        fs = self.sensor_data["Flood"]["status"]
        qs = self.sensor_data["Earthquake"]["status"]
        self.flood_status_lbl.config(text=f"Flood: {fs}",
                                     foreground="red" if fs=="DANGER" else "green")
        self.quake_status_lbl.config(text=f"Quake: {qs}",
                                     foreground="red" if qs=="DANGER" else "green")

    def _check_alerts(self):
        if self.sensor_data["Flood"]["status"] == "DANGER":
            self.add_alert(f"⚠️ Flood >200cm ({self.sensor_data['Flood']['water_level']:.0f}cm)")
        if self.sensor_data["Earthquake"]["status"] == "DANGER":
            se = self.sensor_data["Earthquake"]["seismic_activity"]
            self.add_alert(f"⚠️ Quake >4.5 Richter ({se:.1f})")

        self._update_probabilities()

    def add_alert(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.alert_list.insert(0, f"[{ts}] {msg}")
        if self.alert_list.size()>10:
            self.alert_list.delete(10)

    def create_map(self):
        coords = self.locations[self.current_location]["coords"]
        m = folium.Map(location=coords, zoom_start=12)
        for name,data in self.locations.items():
            folium.Marker(data["coords"], popup=name).add_to(m)
        folium.Marker(coords, icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)

        if self.sensor_data["Flood"]["status"]=="DANGER":
            folium.Circle(location=coords, radius=2000,
                          color="red", fill=True, popup="Flood Zone").add_to(m)

        locations = list(self.locations.keys())
        html = """
        <div style="position: fixed; 
                    top: 10px; 
                    left: 50px; 
                    z-index:9999; 
                    font-size:14px;">
        <select id="location-select" onchange="window.location.href=this.value">
        """
        for location in locations:
            lat, lon = self.locations[location]["coords"]
            url = f"https://www.google.com/maps/@?api=1&map_action=map&center={lat},{lon}&zoom=12&basemap=satellite"
            html += f'<option value="{url}">{location}</option>'
        html += """
                </div>
                """
        m.get_root().html.add_child(folium.Element(html))

        m.save("map.html")
        webbrowser.open("map.html")

    def dispatch_drones(self):
        messagebox.showinfo("Drones", f"🚁 Drones to {self.current_location} dispatched!")

if __name__ == "__main__":
    root = tk.Tk()
    app = DisasterResponseGUI(root)
    root.mainloop()