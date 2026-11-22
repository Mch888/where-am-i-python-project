# where-am-i-locator

Zero-dependency Python library and CLI to get your real physical latitude and longitude using native OS location services and Wi-Fi BSSID fallback—completely bypassing VPN IP addresses.

## Installation
```bash
pip install where-am-i-locator
```

## Python Usage
```python
from where_am_i_locator import Locator

# Default: tries OS location services ('gps'), falls back to 'wifi'
print(Locator.where_am_i())

# Take 5 readings 1 second apart and return the average + timestamped history
print(Locator.where_am_i(method="all", test_length=5, delay=1))
```

### Parameters
* `method` (`"all"` | `"gps"` | `"wifi"`): Location source to use (default `"all"`).
* `timeout` (`int`): Seconds to wait for OS location lock (default `10`).
* `ask_permission` (`bool`): Allow OS permission prompt if not already granted (default `True`).
* `test_length` (`int`): Number of samples to collect and average (default `1`).
* `delay` (`float`): Seconds between samples when `test_length > 1` (default `1`).

## CLI Usage
```bash
where-am-i
where-am-i --method wifi --test-length 3 --delay 0.5
```
