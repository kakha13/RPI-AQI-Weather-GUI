import tkinter as tk
from datetime import datetime
import requests
import json
import subprocess
import time

# --- CONFIGURATION ---
AQI_API_URL = "https://cometer.kakha13.link/api/get/location/7"
WEATHER_API_KEY = "--------------------------------"  # Get from https://openweathermap.org/api
CITY = "Tbilisi"  # Change to your city
UNITS = "metric"   # Use "imperial" for Fahrenheit
UPDATE_INTERVAL = 300000  # Update every 5 minutes (in ms)
# Display rotation: "left", "right", "inverted", or "normal"/None
DISPLAY_ROTATION = "normal"
# Optional: set the display output name (e.g. "DSI-1", "HDMI-1"); auto-detected if None
DISPLAY_OUTPUT = None

class WeatherAQIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pi Zero Weather & AQI")
        # Fullscreen mode
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')
        self.root.bind("<Escape>", lambda e: root.quit())  # Press Esc to exit

        # Prevent "x" symbol from appearing on touch/click outside widgets
        self.root.bind("<Button-1>", lambda e: "break")
        self.root.bind("<ButtonRelease-1>", lambda e: "break")

        # Remove any window border for true fullscreen
        self.root.configure(highlightthickness=0, borderwidth=0)

        # Apply display rotation before querying screen size
        self.apply_display_rotation()

        # Get screen dimensions for dynamic sizing
        self.root.update_idletasks()
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # Force geometry to match screen size
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        
        # Detect orientation: portrait (height > width) or landscape
        self.is_portrait = self.screen_height > self.screen_width
        
        # Use shorter dimension for font scaling to ensure fit
        self.base_dim = min(self.screen_width, self.screen_height)
        
        self.calculate_font_sizes()
        self.build_ui()

        # Bind resize event to recalculate sizes
        self.root.bind('<Configure>', self.on_resize)

        # Initialize
        self.update_clock()
        self.get_aqi_data()
        self.get_weather_data()

    def calculate_font_sizes(self):
        """Calculate dynamic font sizes based on screen size and orientation"""
        if self.is_portrait:
            # Portrait mode - use width as constraint, content stacks vertically
            self.base_font_clock = max(24, min(48, int(self.base_dim * 0.12)))
            self.base_font_date = max(10, min(16, int(self.base_dim * 0.04)))
            self.base_font_location = max(9, min(14, int(self.base_dim * 0.035)))
            self.base_font_weather_icon = max(28, min(50, int(self.base_dim * 0.12)))
            self.base_font_weather_temp = max(20, min(36, int(self.base_dim * 0.09)))
            self.base_font_weather_desc = max(9, min(14, int(self.base_dim * 0.035)))
            self.base_font_aqi_label = max(10, min(16, int(self.base_dim * 0.04)))
            self.base_font_aqi_value = max(28, min(48, int(self.base_dim * 0.12)))
            self.base_font_particles_label = max(10, min(16, int(self.base_dim * 0.04)))
            self.base_font_pm_label = max(8, min(12, int(self.base_dim * 0.028)))
            self.base_font_pm_value = max(11, min(16, int(self.base_dim * 0.04)))
            self.base_font_status = max(8, min(11, int(self.base_dim * 0.025)))
        else:
            # Landscape mode - optimized for 480x320 screens
            self.base_font_clock = max(20, min(40, int(self.screen_height * 0.12)))
            self.base_font_date = max(10, min(14, int(self.screen_height * 0.04)))
            self.base_font_location = max(9, min(12, int(self.screen_height * 0.035)))
            self.base_font_weather_icon = max(32, min(56, int(self.screen_height * 0.15)))
            self.base_font_weather_temp = max(20, min(38, int(self.screen_height * 0.11)))
            self.base_font_weather_desc = max(10, min(14, int(self.screen_height * 0.04)))
            self.base_font_aqi_label = max(10, min(14, int(self.screen_height * 0.04)))
            self.base_font_aqi_value = max(28, min(52, int(self.screen_height * 0.14)))
            self.base_font_particles_label = max(9, min(12, int(self.screen_height * 0.035)))
            self.base_font_pm_label = max(8, min(11, int(self.screen_height * 0.03)))
            self.base_font_pm_value = max(12, min(18, int(self.screen_height * 0.05)))
            self.base_font_status = max(8, min(10, int(self.screen_height * 0.028)))

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
            # Give X a moment to apply the rotation before querying size
            time.sleep(0.1)
        except Exception:
            return

    def build_ui(self):
        """Build the UI layout based on orientation"""
        # Main container frame - full screen
        self.main_frame = tk.Frame(self.root, bg='black', highlightthickness=0, borderwidth=0)
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Top section - Clock and Date (centered)
        top_frame = tk.Frame(self.main_frame, bg='black')
        top_frame.pack(side="top", fill="x", pady=(0, 0))

        # Clock Label
        self.lbl_clock = tk.Label(top_frame, font=("Arial", self.base_font_clock, "bold"), fg="white", bg="black")
        self.lbl_clock.pack()

        # Date Label
        self.lbl_date = tk.Label(top_frame, font=("Arial", self.base_font_date), fg="#aaaaaa", bg="black")
        self.lbl_date.pack(pady=(0, 0))

        # Location Label
        self.lbl_location = tk.Label(top_frame, font=("Arial", self.base_font_location, "bold"), fg="#4CAF50", bg="black")
        self.lbl_location.pack(pady=(0, 0))

        # Content container
        content_frame = tk.Frame(self.main_frame, bg='black')
        content_frame.pack(side="top", fill="both", expand=True, pady=(0, 0))

        if self.is_portrait:
            # PORTRAIT MODE: Stack Weather on top, AQI below
            self.build_portrait_layout(content_frame)
        else:
            # LANDSCAPE MODE: Weather left, AQI right
            self.build_landscape_layout(content_frame)

        # Status/Error Label (bottom)
        self.lbl_status = tk.Label(self.main_frame, font=("Arial", self.base_font_status), fg="#ff4444", bg="black")
        self.lbl_status.pack(side="bottom", pady=(0, 0))

    def build_portrait_layout(self, parent):
        """Build portrait layout - content stacked vertically"""
        # Weather section (top half)
        weather_frame = tk.Frame(parent, bg='black')
        weather_frame.pack(side="top", fill="both", expand=True)

        tk.Label(weather_frame, text="Weather", font=("Arial", self.base_font_aqi_label, "bold"), fg="#aaaaaa", bg="black").pack(pady=(0, 3))

        # Weather row - icon, temp, desc side by side for compact display
        weather_row = tk.Frame(weather_frame, bg='black')
        weather_row.pack(fill="x", expand=True)

        self.lbl_weather_symbol = tk.Label(weather_row, font=("Arial", self.base_font_weather_icon), fg="gold", bg="black")
        self.lbl_weather_symbol.pack(side="left", padx=(10, 5))

        weather_info = tk.Frame(weather_row, bg='black')
        weather_info.pack(side="left", fill="both", expand=True)

        self.lbl_weather_temp = tk.Label(weather_info, font=("Arial", self.base_font_weather_temp, "bold"), fg="white", bg="black", anchor="w")
        self.lbl_weather_temp.pack(anchor="w")

        self.lbl_weather_desc = tk.Label(weather_info, font=("Arial", self.base_font_weather_desc, "italic"), fg="#aaaaaa", bg="black", anchor="w")
        self.lbl_weather_desc.pack(anchor="w")

        # Separator
        tk.Frame(parent, bg='#333333', height=1).pack(fill="x", pady=8)

        # AQI section (bottom half)
        aqi_frame = tk.Frame(parent, bg='black')
        aqi_frame.pack(side="top", fill="both", expand=True)

        # AQI row - label and value side by side
        aqi_top = tk.Frame(aqi_frame, bg='black')
        aqi_top.pack(fill="x")

        self.lbl_aqi_label = tk.Label(aqi_top, text="AQI", font=("Arial", self.base_font_aqi_label, "bold"), fg="#aaaaaa", bg="black")
        self.lbl_aqi_label.pack(side="left", padx=(10, 10))

        self.lbl_aqi_value = tk.Label(aqi_top, font=("Arial", self.base_font_aqi_value, "bold"), fg="white", bg="black")
        self.lbl_aqi_value.pack(side="left")

        # Particles section
        particles_label = tk.Label(aqi_frame, text="Particles", font=("Arial", self.base_font_particles_label, "bold"), fg="#aaaaaa", bg="black")
        particles_label.pack(pady=(8, 3))

        # Particles container - horizontal layout
        particles_container = tk.Frame(aqi_frame, bg='black')
        particles_container.pack()

        # PM2.5
        pm25_frame = tk.Frame(particles_container, bg='black')
        pm25_frame.pack(side="left", padx=8)
        tk.Label(pm25_frame, text="PM2.5", font=("Arial", self.base_font_pm_label), fg="#aaaaaa", bg="black").pack()
        self.lbl_pm25 = tk.Label(pm25_frame, font=("Arial", self.base_font_pm_value, "bold"), fg="#FF9800", bg="black")
        self.lbl_pm25.pack()

        # PM10
        pm10_frame = tk.Frame(particles_container, bg='black')
        pm10_frame.pack(side="left", padx=8)
        tk.Label(pm10_frame, text="PM10", font=("Arial", self.base_font_pm_label), fg="#aaaaaa", bg="black").pack()
        self.lbl_pm10 = tk.Label(pm10_frame, font=("Arial", self.base_font_pm_value, "bold"), fg="#FF5722", bg="black")
        self.lbl_pm10.pack()

        # PM1
        pm1_frame = tk.Frame(particles_container, bg='black')
        pm1_frame.pack(side="left", padx=8)
        tk.Label(pm1_frame, text="PM1", font=("Arial", self.base_font_pm_label), fg="#aaaaaa", bg="black").pack()
        self.lbl_pm1 = tk.Label(pm1_frame, font=("Arial", self.base_font_pm_value, "bold"), fg="#9C27B0", bg="black")
        self.lbl_pm1.pack()

    def build_landscape_layout(self, parent):
        """Build landscape layout - content side by side, centered and filling space"""
        # LEFT SIDE - Weather section
        left_frame = tk.Frame(parent, bg='black')
        left_frame.pack(side="left", fill="both", expand=True, padx=0)

        tk.Label(
            left_frame,
            text="Weather",
            font=("Arial", self.base_font_aqi_label, "bold"),
            fg="#aaaaaa",
            bg="black",
        ).pack(expand=True, pady=0)

        self.lbl_weather_symbol = tk.Label(left_frame, font=("Arial", self.base_font_weather_icon), fg="gold", bg="black")
        self.lbl_weather_symbol.pack(expand=True, pady=0)

        self.lbl_weather_temp = tk.Label(left_frame, font=("Arial", self.base_font_weather_temp, "bold"), fg="white", bg="black")
        self.lbl_weather_temp.pack(expand=True, pady=0)

        self.lbl_weather_desc = tk.Label(left_frame, font=("Arial", self.base_font_weather_desc, "italic"), fg="#aaaaaa", bg="black")
        self.lbl_weather_desc.pack(expand=True, pady=0)

        # RIGHT SIDE - AQI section
        right_frame = tk.Frame(parent, bg='black')
        right_frame.pack(side="right", fill="both", expand=True, padx=0)

        self.lbl_aqi_label = tk.Label(right_frame, text="AQI", font=("Arial", self.base_font_aqi_label, "bold"), fg="#aaaaaa", bg="black")
        self.lbl_aqi_label.pack(expand=True, pady=0)

        self.lbl_aqi_value = tk.Label(right_frame, font=("Arial", self.base_font_aqi_value, "bold"), fg="white", bg="black")
        self.lbl_aqi_value.pack(expand=True, pady=0)

        particles_label = tk.Label(right_frame, text="Particles", font=("Arial", self.base_font_particles_label, "bold"), fg="#aaaaaa", bg="black")
        particles_label.pack(expand=True, pady=0)

        particles_container = tk.Frame(right_frame, bg='black')
        particles_container.pack(expand=True)

        # PM2.5
        pm25_frame = tk.Frame(particles_container, bg='black')
        pm25_frame.pack(side="left", padx=4)
        tk.Label(pm25_frame, text="PM2.5", font=("Arial", self.base_font_pm_label), fg="#aaaaaa", bg="black").pack()
        self.lbl_pm25 = tk.Label(pm25_frame, font=("Arial", self.base_font_pm_value, "bold"), fg="#FF9800", bg="black")
        self.lbl_pm25.pack()

        # PM10
        pm10_frame = tk.Frame(particles_container, bg='black')
        pm10_frame.pack(side="left", padx=4)
        tk.Label(pm10_frame, text="PM10", font=("Arial", self.base_font_pm_label), fg="#aaaaaa", bg="black").pack()
        self.lbl_pm10 = tk.Label(pm10_frame, font=("Arial", self.base_font_pm_value, "bold"), fg="#FF5722", bg="black")
        self.lbl_pm10.pack()

        # PM1
        pm1_frame = tk.Frame(particles_container, bg='black')
        pm1_frame.pack(side="left", padx=4)
        tk.Label(pm1_frame, text="PM1", font=("Arial", self.base_font_pm_label), fg="#aaaaaa", bg="black").pack()
        self.lbl_pm1 = tk.Label(pm1_frame, font=("Arial", self.base_font_pm_value, "bold"), fg="#9C27B0", bg="black")
        self.lbl_pm1.pack()

    def on_resize(self, event=None):
        """Handle window resize to recalculate font sizes"""
        if event and event.widget == self.root:
            new_width = self.root.winfo_width()
            new_height = self.root.winfo_height()
            
            # Only update if significant change
            if abs(new_width - self.screen_width) > 10 or abs(new_height - self.screen_height) > 10:
                self.screen_width = new_width
                self.screen_height = new_height
                self.base_dim = min(self.screen_width, self.screen_height)
                
                # Recalculate font sizes
                self.calculate_font_sizes()
                
                # Update fonts
                self.lbl_clock.config(font=("Arial", self.base_font_clock, "bold"))
                self.lbl_date.config(font=("Arial", self.base_font_date))
                self.lbl_location.config(font=("Arial", self.base_font_location, "bold"))
                self.lbl_weather_symbol.config(font=("Arial", self.base_font_weather_icon))
                self.lbl_weather_temp.config(font=("Arial", self.base_font_weather_temp, "bold"))
                self.lbl_weather_desc.config(font=("Arial", self.base_font_weather_desc, "italic"))
                self.lbl_aqi_label.config(font=("Arial", self.base_font_aqi_label, "bold"))
                self.lbl_aqi_value.config(font=("Arial", self.base_font_aqi_value, "bold"))
                self.lbl_pm25.config(font=("Arial", self.base_font_pm_value, "bold"))
                self.lbl_pm10.config(font=("Arial", self.base_font_pm_value, "bold"))
                self.lbl_pm1.config(font=("Arial", self.base_font_pm_value, "bold"))
                self.lbl_status.config(font=("Arial", self.base_font_status))

    def update_clock(self):
        now = datetime.now()
        self.lbl_clock.config(text=now.strftime("%H:%M:%S"))
        self.lbl_date.config(text=now.strftime("%a %b %d"))
        self.root.after(1000, self.update_clock)

    def get_aqi_level(self, aqi_value):
        """Determine AQI level based on value"""
        if aqi_value <= 50:
            return "Good", "#4CAF50"
        elif aqi_value <= 100:
            return "Moderate", "#F4CF48"
        elif aqi_value <= 150:
            return "Unhealthy (Sensitive)", "#FF9800"
        elif aqi_value <= 200:
            return "Unhealthy", "#FF5722"
        elif aqi_value <= 300:
            return "Very Unhealthy", "#9C27B0"
        else:
            return "Hazardous", "#F44336"

    def get_weather_data(self):
        """Fetch weather data from OpenWeatherMap API"""
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units={UNITS}"
            res = requests.get(url, timeout=10).json()
            
            temp = res['main']['temp']
            desc = res['weather'][0]['description']
            w_id = res['weather'][0]['id']
            
            # Map OpenWeather ID to Unicode Symbols
            icon = "❓"
            if w_id >= 200 and w_id <= 232: icon = "⛈"  # Thunder
            elif w_id >= 300 and w_id <= 321: icon = "🌦"  # Drizzle
            elif w_id >= 500 and w_id <= 531: icon = "🌧"  # Rain
            elif w_id >= 600 and w_id <= 622: icon = "❄"  # Snow
            elif w_id == 800: icon = "☀️"  # Clear
            elif w_id > 800: icon = "☁️"  # Clouds

            self.lbl_weather_symbol.config(text=icon)
            self.lbl_weather_temp.config(text=f"{round(temp)}°C")
            self.lbl_weather_desc.config(text=desc.capitalize())
            
        except Exception as e:
            self.lbl_weather_temp.config(text="N/A")
            self.lbl_weather_desc.config(text="Weather unavailable")
            self.lbl_weather_symbol.config(text="❓")
        
        # Schedule next update
        self.root.after(UPDATE_INTERVAL, self.get_weather_data)

    def get_aqi_data(self):
        try:
            response = requests.get(AQI_API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Extract location info
            info = data.get('info', {})
            city = info.get('city', 'N/A')
            name = info.get('name', 'N/A')
            # Show full location name
            if name and name != 'N/A':
                location_text = f"{city} - {name}"
            else:
                location_text = city
            self.lbl_location.config(text=location_text)

            # Extract AQI data
            aqi = data.get('aqi', {})
            aqi_data = aqi.get('data', {})

            # Get overall AQI value
            overall_aqi = aqi_data.get('overall', 0)
            level, color = self.get_aqi_level(overall_aqi)
            
            # Use API color if available, otherwise use calculated color
            api_color = data.get('color', color)
            
            self.lbl_aqi_value.config(text=f"{overall_aqi}", fg=api_color)
            self.lbl_aqi_label.config(text=f"AQI: {level}", fg=api_color)

            # Update PM values
            pm25 = aqi_data.get('PMS25', 0)
            pm10 = aqi_data.get('PMS10', 0)
            pm1 = aqi_data.get('PMS1', 0)

            self.lbl_pm25.config(text=f"{pm25}")
            self.lbl_pm10.config(text=f"{pm10}")
            self.lbl_pm1.config(text=f"{pm1}")

            # Clear status if successful
            self.lbl_status.config(text="")

        except requests.exceptions.RequestException as e:
            self.lbl_status.config(text=f"Connection Error: {str(e)}")
            self.lbl_aqi_value.config(text="--", fg="#ff4444")
        except KeyError as e:
            self.lbl_status.config(text=f"Data Error: Missing key {str(e)}")
        except Exception as e:
            self.lbl_status.config(text=f"Error: {str(e)}")
            self.lbl_aqi_value.config(text="--", fg="#ff4444")

        # Schedule next update
        self.root.after(UPDATE_INTERVAL, self.get_aqi_data)

if __name__ == "__main__":
    root = tk.Tk()
    # Hide cursor for a cleaner look
    root.config(cursor="none")
    app = WeatherAQIApp(root)
    root.mainloop()
