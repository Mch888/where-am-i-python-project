from datetime import datetime, timezone
import json
import platform
import re
import subprocess
import time
import urllib.request


class Locator:

  @classmethod
  def where_am_i(
      cls, method="all", timeout=10, ask_permission=True, test_length=1, delay=1
  ):
    system = platform.system()

    if method not in ("all", "gps", "wifi"):
      return {
          "latitude": None,
          "longitude": None,
          "source": "",
          "history": [],
          "errors": (
              f"Invalid method: '{method}'. Choose from 'all', 'gps', or"
              " 'wifi'."
          ),
      }

    if test_length < 1:
      return {
          "latitude": None,
          "longitude": None,
          "source": "",
          "history": [],
          "errors": "test_length must be at least 1.",
      }

    history = []
    last_source = ""

    for i in range(test_length):
      coords = None
      source = ""

      if method in ("all", "gps") and (ask_permission or cls.has_permission()):
        if system == "Windows":
          coords = cls._windows(timeout)
        elif system == "Darwin":
          coords = cls._macos(timeout)
        elif system == "Linux":
          coords = cls._linux(timeout)

        if coords:
          source = "gps"

      if not coords and method in ("all", "wifi"):
        coords = cls._wifi_fallback(system)
        if coords:
          source = "wifi"

      if coords:
        lat, lon = coords
        ts = datetime.now(timezone.utc).isoformat()
        history.append({
            "latitude": lat,
            "longitude": lon,
            "source": source,
            "timestamp": ts,
        })
        last_source = source

      if i < test_length - 1 and delay > 0:
        time.sleep(delay)

    if history:
      avg_lat = sum(entry["latitude"] for entry in history) / len(history)
      avg_lon = sum(entry["longitude"] for entry in history) / len(history)
      return {
          "latitude": avg_lat,
          "longitude": avg_lon,
          "source": last_source,
          "history": history,
          "errors": "",
      }

    return {
        "latitude": None,
        "longitude": None,
        "source": "",
        "history": [],
        "errors": f"Location unavailable using method='{method}' on {system}.",
    }

  @staticmethod
  def has_permission():
    system = platform.system()
    if system == "Windows":
      ps = (
          "Get-ItemProperty -Path"
          " 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location'"
          " -Name Value | Select-Object -ExpandProperty Value"
      )
      res = subprocess.run(
          ["powershell", "-NoProfile", "-Command", ps],
          capture_output=True,
          text=True,
      )
      return res.stdout.strip() == "Allow"
    return True

  @classmethod
  def _wifi_fallback(cls, system):
    aps = []
    try:
      if system == "Windows":
        out = subprocess.check_output(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            text=True,
            errors="ignore",
        )
        bssids = re.findall(r"BSSID \d+\s*:\s*([0-9a-fA-F:]{17})", out)
        signals = re.findall(r"Signal\s*:\s*(\d+)%", out)
        for mac, sig in zip(bssids, signals):
          rssi = int((int(sig) / 2) - 100)
          aps.append({"macAddress": mac, "signalStrength": rssi})

      elif system == "Darwin":
        out = subprocess.check_output(
            ["system_profiler", "SPAirPortDataType"],
            text=True,
            errors="ignore",
        )
        bssids = re.findall(r"BSSID:\s*([0-9a-fA-F:]{17})", out)
        for mac in bssids:
          aps.append({"macAddress": mac})

      elif system == "Linux":
        out = subprocess.check_output(
            ["nmcli", "-t", "-f", "BSSID,SIGNAL", "dev", "wifi"],
            text=True,
            errors="ignore",
        )
        for line in out.splitlines():
          parts = line.replace("\\:", ":").rsplit(":", 1)
          if len(parts) == 2:
            mac, sig = parts
            if len(mac) == 17:
              rssi = int((int(sig) / 2) - 100)
              aps.append({"macAddress": mac, "signalStrength": rssi})

      if not aps:
        return None

      first_ap = next(iter(aps))
      bssid = first_ap["macAddress"]
      url = f"https://mylnikov.org{bssid}"
      req = urllib.request.Request(
          url, headers={"User-Agent": "PythonLocator/1.0"}
      )
      with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode())
        if data.get("result") == 200:
          return float(data["data"]["lat"]), float(data["data"]["lon"])
    except Exception:
      return None
    return None

  @staticmethod
  def _windows(timeout):
    ps_script = f"""
        Add-Type -AssemblyName System.Device
        $watcher = New-Object System.Device.Location.GeoCoordinateWatcher
        $watcher.Start()
        $limit = {timeout * 5}
        $count = 0
        while (($watcher.Status -ne 'Ready') -and ($watcher.Permission -ne 'Denied') -and ($count -lt $limit)) {{
            Start-Sleep -Milliseconds 200
            $count++
        }}
        if ($watcher.Status -eq 'Ready') {{
            $c = $watcher.Position.Location
            @{{lat=$c.Latitude; lon=$c.Longitude}} | ConvertTo-Json
        }}
        """
    res = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True,
        text=True,
    )
    if res.stdout.strip():
      data = json.loads(res.stdout)
      return float(data["lat"]), float(data["lon"])
    return None

  @staticmethod
  def _macos(timeout):
    swift_code = f"""
        import CoreLocation
        import Foundation
        class Loc: NSObject, CLLocationManagerDelegate {{
            let mgr = CLLocationManager()
            override init() {{
                super.init()
                mgr.delegate = self
                mgr.startUpdatingLocation()
            }}
            func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {{
                if let loc = locations.last {{
                    print("\\(loc.coordinate.latitude),\\(loc.coordinate.longitude)")
                    exit(0)
                }}
            }}
        }}
        let l = Loc()
        RunLoop.main.run(until: Date(timeIntervalSinceNow: {timeout}))
        """
    res = subprocess.run(
        ["swift", "-e", swift_code], capture_output=True, text=True
    )
    if "," in res.stdout:
      lat, lon = res.stdout.strip().split(",")
      return float(lat), float(lon)
    return None

  @staticmethod
  def _linux(timeout):
    res = subprocess.run(
        ["/usr/libexec/geoclue-2.0/demos/where-am-i", "-t", str(timeout)],
        capture_output=True,
        text=True,
    )
    lat = re.search(r"Latitude:\s+([-\d.]+)", res.stdout)
    lon = re.search(r"Longitude:\s+([-\d.]+)", res.stdout)
    if lat and lon:
      return float(lat.group(1)), float(lon.group(1))
    return None
