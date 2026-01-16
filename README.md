# Raspberry Pi Weather GUI

A collection of fullscreen weather display applications for Raspberry Pi Zero (or other Raspberry Pi models). Includes applications for displaying weather information from OpenWeatherMap API and Air Quality Index (AQI) data from custom API endpoints.

## Applications

### 1. `weather.py` - OpenWeatherMap Weather Display
Displays current time, date, and weather information using OpenWeatherMap API.

**Features:**
- **Fullscreen Display**: Runs in fullscreen mode optimized for touchscreen displays
- **Real-time Clock**: Displays current time and date
- **Weather Information**: Shows current temperature, weather description, and weather icons
- **Auto-update**: Weather updates every 10 minutes automatically
- **Touchscreen Optimized**: Configured for Raspberry Pi touchscreen displays

### 2. `weather_aqi.py` - Weather & Air Quality Index Display
Displays weather and Air Quality Index (AQI) information from a custom API endpoint.

**Features:**
- **Fullscreen Display**: Runs in fullscreen mode optimized for touchscreen displays
- **Real-time Clock**: Displays current time and date
- **Location Information**: Shows city and station name
- **Weather Display**: Shows current weather temperature, description, and weather icons
- **AQI Display**: Shows overall Air Quality Index with color-coded levels
- **PM Values**: Displays PM2.5, PM10, and PM1 particulate matter readings
- **Auto-update**: Data updates every 5 minutes automatically
- **Color-coded AQI**: Uses API-provided colors for AQI levels (Good, Moderate, Unhealthy, etc.)
- **Auto-resizing**: Dynamically adjusts font sizes and layout to fit any screen size

## Prerequisites

- Raspberry Pi (tested on Pi Zero)
- Raspberry Pi OS installed
- Touchscreen display connected
- Internet connection for weather API
- Python 3 installed

## Installation

### 1. Install Required System Packages

```bash
sudo apt update
sudo apt install xserver-xorg-video-fbdev python3-tk python3-requests
```

### 2. Configure X11 for Touchscreen Display

Create the X11 configuration file for the framebuffer device:

```bash
sudo nano /usr/share/X11/xorg.conf.d/99-fbdev.conf
```

Add the following content:

```
Section "Device"
  Identifier "touchscreen"
  Driver "fbdev"
  Option "fbdev" "/dev/fb1"
EndSection

Section "Screen"
  Identifier "Screen0"
  Device "touchscreen"
EndSection

Section "ServerLayout"
  Identifier "Layout0"
  Screen "Screen0"
EndSection
```

Save and exit (Ctrl+X, then Y, then Enter).

### 3. Configure GPU Memory

Edit the boot configuration file:

```bash
sudo nano /boot/firmware/config.txt
```

Make the following changes:
- Change `gpu_mem=256` to `gpu_mem=64` or `gpu_mem=128`
- Ensure `dtoverlay=vc4-kms-v3d` remains commented out (with `#` at the start)

Save and exit, then reboot:

```bash
sudo reboot
```

### 4. Install the Application

Clone or copy the application files to your Raspberry Pi:

```bash
# If using git
git clone <repository-url>
cd RPI-Weather-GUI

# Or copy the Python files to your desired location, e.g.:
# /home/username/weather.py
# /home/username/weather_aqi.py
```

### 5. Configure Applications

#### For `weather.py` - OpenWeatherMap Configuration

Edit `weather.py` and update the following variables:

```python
API_KEY = "your_openweathermap_api_key"  # Get from https://openweathermap.org/api
CITY = "YourCity"  # Change to your city name
UNITS = "metric"   # Use "imperial" for Fahrenheit
```

**To get an API key:**
1. Sign up at [OpenWeatherMap](https://openweathermap.org/api)
2. Navigate to API keys section
3. Copy your API key and paste it in `weather.py`

#### For `weather_aqi.py` - AQI and Weather API Configuration

Edit `weather_aqi.py` and update the following variables:

```python
AQI_API_URL = "https://cometer.kakha13.link/api/get/location/7"  # Change location ID if needed
WEATHER_API_KEY = "your_openweathermap_api_key"  # Get from https://openweathermap.org/api
CITY = "Tbilisi"  # Change to your city name
UNITS = "metric"   # Use "imperial" for Fahrenheit
```

The AQI application uses:
- **Custom AQI API endpoint** that provides:
  - Location information (city, station name)
  - AQI data (overall index, PM2.5, PM10, PM1)
- **OpenWeatherMap API** for weather data (temperature, description, icons)

## Usage

### Starting the Applications

After configuring everything, start either application with:

**For OpenWeatherMap Weather Display:**
```bash
startx /usr/bin/python3 /home/username/weather.py
```

**For Weather & AQI Display:**
```bash
startx /usr/bin/python3 /home/username/weather_aqi.py
```

**Note:** Replace `/home/username/weather.py` or `/home/username/weather_aqi.py` with the actual path to your Python file.

### Exiting the Application

Press **Esc** key to exit the application.

### Auto-start on Boot

There are several methods to automatically start the GUI application when the Raspberry Pi boots. Choose the method that best fits your setup.

#### Method 1: Using systemd Service (Recommended)

This is the most reliable method and works with all Raspberry Pi OS versions.

1. Create a systemd service file:

```bash
sudo nano /etc/systemd/system/weather-gui.service
```

2. Add the following content (replace `/home/username/weather_aqi.py` with your actual file path):

```ini
[Unit]
Description=Weather AQI GUI Application
After=network.target graphical.target

[Service]
Type=simple
User=pi
Environment=DISPLAY=:0
ExecStart=/usr/bin/python3 /home/username/weather_aqi.py
Restart=always
RestartSec=10

[Install]
WantedBy=graphical.target
```

3. Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable weather-gui.service
sudo systemctl start weather-gui.service
```

4. Check the status:

```bash
sudo systemctl status weather-gui.service
```

**To stop the service:**
```bash
sudo systemctl stop weather-gui.service
```

**To disable auto-start:**
```bash
sudo systemctl disable weather-gui.service
```

#### Method 2: Using .xinitrc (For X11-based systems)

1. Create or edit the `.xinitrc` file:

```bash
nano ~/.xinitrc
```

2. Add the following line (replace with your actual file path):

```bash
/usr/bin/python3 /home/username/weather_aqi.py
```

3. Configure X to start automatically on boot. Edit the autologin configuration:

```bash
sudo nano /etc/systemd/system/getty@tty1.service.d/autologin.conf
```

Ensure it contains:
```ini
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin pi --noclear %I $TERM
```

4. Add to `.bashrc` to start X on login:

```bash
nano ~/.bashrc
```

Add at the end:
```bash
if [[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]]; then
    startx
fi
```

#### Method 3: Using autostart Directory (For Desktop Environments)

If you're using a desktop environment like LXDE:

1. Create the autostart directory if it doesn't exist:

```bash
mkdir -p ~/.config/autostart
```

2. Create a desktop entry file:

```bash
nano ~/.config/autostart/weather-gui.desktop
```

3. Add the following content:

```ini
[Desktop Entry]
Type=Application
Name=Weather GUI
Exec=/usr/bin/python3 /home/username/weather_aqi.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
```

#### Method 4: Using rc.local (Legacy Method)

1. Edit the rc.local file:

```bash
sudo nano /etc/rc.local
```

2. Add before `exit 0`:

```bash
# Wait for X server to be ready
sleep 10
su - pi -c "export DISPLAY=:0 && startx /usr/bin/python3 /home/username/weather_aqi.py &"
```

**Note:** Replace `/home/username/weather_aqi.py` with the actual path to your Python file in all methods above. Also replace `pi` with your actual username if different.

**For `weather.py` instead of `weather_aqi.py`:** Simply replace the file path in any of the methods above.

## Configuration Options

### `weather.py` Configuration

You can customize the OpenWeatherMap application by editing the configuration section:

- `API_KEY`: Your OpenWeatherMap API key
- `CITY`: City name for weather data
- `UNITS`: Temperature units (`"metric"` for Celsius, `"imperial"` for Fahrenheit)
- `UPDATE_INTERVAL`: Weather update interval in milliseconds (default: 600000 = 10 minutes)

### `weather_aqi.py` Configuration

You can customize the AQI application by editing the configuration section:

- `AQI_API_URL`: AQI API endpoint URL (default: `https://cometer.kakha13.link/api/get/location/7`)
- `WEATHER_API_KEY`: Your OpenWeatherMap API key (get from https://openweathermap.org/api)
- `CITY`: City name for weather data
- `UNITS`: Temperature units (`"metric"` for Celsius, `"imperial"` for Fahrenheit)
- `UPDATE_INTERVAL`: Data update interval in milliseconds (default: 300000 = 5 minutes)

## Troubleshooting

### Display Issues

- **Black screen**: Check that `/dev/fb1` exists and is accessible
- **Wrong resolution**: Verify GPU memory settings in `/boot/firmware/config.txt`
- **Touchscreen not working**: Ensure the framebuffer device is correctly configured

### Weather Data Not Loading

**For `weather.py`:**
- **"Offline / Error" message**: 
  - Check internet connection
  - Verify API key is correct
  - Ensure city name is spelled correctly
  - Check OpenWeatherMap API status

**For `weather_aqi.py`:**
- **Connection Error or Data Error messages**:
  - Check internet connection
  - Verify API URL is correct and accessible
  - Ensure the API endpoint is responding (test with `curl https://cometer.kakha13.link/api/get/location/7`)
  - Check that the location ID in the URL is valid

### Application Won't Start

- Ensure Python 3 and tkinter are installed: `sudo apt install python3-tk`
- Check that requests library is installed: `pip3 install requests`
- Verify file permissions: `chmod +x weather.py`

### Performance Issues

- Reduce `UPDATE_INTERVAL` if updates are too frequent
- Lower GPU memory allocation if experiencing memory issues
- Ensure stable internet connection for API calls

## File Structure

```
RPI-Weather-GUI/
├── weather.py          # OpenWeatherMap weather display application
├── weather_aqi.py      # Weather & AQI display application
└── README.md          # This file
```

## License

This project is open source and available for personal use.

## Credits

- Weather data provided by [OpenWeatherMap](https://openweathermap.org/)
- AQI data provided by custom API endpoint (https://cometer.kakha13.link/api/get/location/7)
- Built with Python and tkinter
