import argparse
import json
from .core import Locator


def main():
  parser = argparse.ArgumentParser(
      description="Get physical latitude and longitude bypassing VPN IPs."
  )
  parser.add_argument(
      "-m",
      "--method",
      choices=["all", "gps", "wifi"],
      default="all",
      help="Location method: 'all', 'gps', or 'wifi' (default: all)",
  )
  parser.add_argument(
      "-t",
      "--test-length",
      type=int,
      default=1,
      help="Number of readings to average (default: 1)",
  )
  parser.add_argument(
      "-d",
      "--delay",
      type=float,
      default=1.0,
      help="Delay in seconds between readings (default: 1.0)",
  )
  parser.add_argument(
      "--no-ask",
      action="store_true",
      help="Do not trigger OS permission prompt if not already granted",
  )

  args = parser.parse_args()
  result = Locator.where_am_i(
      method=args.method,
      ask_permission=not args.no_ask,
      test_length=args.test_length,
      delay=args.delay,
  )
  print(json.dumps(result, indent=2))


if __name__ == "__main__":
  main()
