"""
Garmin APIの生レスポンスを確認するスクリプト。
Claude APIは使用しない。

使用方法:
    .venv/bin/python scripts/inspect_garmin.py
    .venv/bin/python scripts/inspect_garmin.py --date 2026-02-24
"""
import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import load_config
from garminconnect import Garmin


def fetch_raw(api: Garmin, target_date: str) -> dict:
    results = {}
    for name, fn in [
        ("sleep",  lambda: api.get_sleep_data(target_date)),
        ("steps",  lambda: api.get_steps_data(target_date)),
        ("stress", lambda: api.get_stress_data(target_date)),
    ]:
        try:
            results[name] = fn()
        except Exception as e:
            results[name] = {"error": str(e)}
    return results


def main():
    parser = argparse.ArgumentParser(description="Garmin APIの生レスポンスを表示する")
    parser.add_argument("--date", default=None, help="対象日付 YYYY-MM-DD（省略時: 昨日）")
    args = parser.parse_args()

    target_date = args.date or (date.today() - timedelta(days=1)).isoformat()

    config = load_config()
    print(f"対象日付: {target_date}")
    print("Garminに接続中...")
    api = Garmin(email=config.garmin_email, password=config.garmin_password)
    api.login()

    print("データ取得中...\n")
    raw = fetch_raw(api, target_date)

    for section, data in raw.items():
        print(f"{'='*40}")
        print(f"# {section.upper()}")
        print(f"{'='*40}")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        print()


if __name__ == "__main__":
    main()
