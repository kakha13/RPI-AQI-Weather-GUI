import tkinter as tk
from datetime import datetime
import requests
import time
import subprocess

# --- CONFIGURATION ---
API_KEY = "--------------------------------" # OpenWeatherMap API key
CITY = "Tbilisi"  # Change to your city
UNITS = "metric"   # Use "imperial" for Fahrenheit
UPDATE_INTERVAL = 600000  # Update weather every 10 minutes (in ms)
# Display rotation: "left", "right", "inverted", or "normal"/None
DISPLAY_ROTATION = "left"
# Optional: set the display output name (e.g. "DSI-1", "HDMI-1"); auto-detected if None
DISPLAY_OUTPUT = None

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pi Zero Weather")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')
        self.root.bind("<Escape>", lambda e: root.quit()) # Press Esc to exit

        self.apply_display_rotation()

        # Layout Frames
        self.top_frame = tk.Frame(root, bg='black')
        self.top_frame.pack(side="top", fill="both", expand=True)
        
        # Clock Label
        self.lbl_clock = tk.Label(self.top_frame, font=("Arial", 50, "bold"), fg="white", bg="black")
        self.lbl_clock.pack(pady=(20, 0))

        # Date Label
        self.lbl_date = tk.Label(self.top_frame, font=("Arial", 15), fg="#aaaaaa", bg="black")
        self.lbl_date.pack()

        # Weather Symbol Label (Unicode symbols)
        self.lbl_symbol = tk.Label(root, font=("Arial", 80), fg="gold", bg="black")
        self.lbl_symbol.pack()

        # Temperature Label
        self.lbl_temp = tk.Label(root, font=("Arial", 40, "bold"), fg="white", bg="black")
        self.lbl_temp.pack()

        # Description Label
        self.lbl_desc = tk.Label(root, font=("Arial", 15, "italic"), fg="#aaaaaa", bg="black")
        self.lbl_desc.pack()

        self.update_clock()
        self.get_weather()

    def get_display_output(self):
        """Return the active display output name from xrandr, if available."""
        try:
            result = subprocess.run(
                ["xrandr", "--query"],
                check=True,
                capture_output=True,
                text=True,
            )
            for line in result.stdout.splitlines():
                if " connected primary" in line:
                    return line.split()[0]
            for line in result.stdout.splitlines():
                if " connected" in line:
                    return line.split()[0]
        except Exception:
            return None
        return None

    def apply_display_rotation(self):
        """Rotate the display using xrandr if configured."""
        rotation = DISPLAY_ROTATION
        if not rotation or rotation == "normal":
            return
        output = DISPLAY_OUTPUT or self.get_display_output()
        if not output:
            return
        try:
            subprocess.run(
                ["xrandr", "--output", output, "--rotate", rotation],
                check=True,
            )
            time.sleep(0.1)
        except Exception:
            return

    def update_clock(self):
        now = datetime.now()
        self.lbl_clock.config(text=now.strftime("%H:%M:%S"))
        self.lbl_date.config(text=now.strftime("%A, %b %d %Y"))
        self.root.after(1000, self.update_clock)

    def get_weather(self):
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units={UNITS}"
            res = requests.get(url).json()
            
            temp = res['main']['temp']
            desc = res['weather'][0]['description']
            w_id = res['weather'][0]['id']
            
            # Map OpenWeather ID to Unicode Symbols
            icon = "❓"
            if w_id >= 200 and w_id <= 232: icon = "⛈" # Thunder
            elif w_id >= 300 and w_id <= 321: icon = "🌦" # Drizzle
            elif w_id >= 500 and w_id <= 531: icon = "🌧" # Rain
            elif w_id >= 600 and w_id <= 622: icon = "❄" # Snow
            elif w_id == 800: icon = "☀️" # Clear
            elif w_id > 800: icon = "☁️" # Clouds

            self.lbl_symbol.config(text=icon)
            self.lbl_temp.config(text=f"{round(temp)}°C")
            self.lbl_desc.config(text=desc.capitalize())
            
        except Exception as e:
            self.lbl_desc.config(text="Offline / Error")
        
        self.root.after(UPDATE_INTERVAL, self.get_weather)

if __name__ == "__main__":
    root = tk.Tk()
    # Adjust cursor (hide it for a cleaner look)
    root.config(cursor="none")
    app = WeatherApp(root)
    root.mainloop()