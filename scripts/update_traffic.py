#!/usr/bin/env python3
"""
به‌روزرسانی داده‌های ترافیک، پلیس، تصادف و حوادث از WazeAPI

Workflow هر ۱۰ دقیقه اجرا می‌شود، اما Scheduler/TTL باعث می‌شود
هر منطقه فقط وقتی واقعاً موعد به‌روزرسانی آن رسیده باشد API را صدا بزند.
"""

import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

import requests

# ============================================================
# تنظیمات مناطق
# jams_interval_min = فاصله به‌روزرسانی ترافیک
# alerts_interval_min = فاصله به‌روزرسانی پلیس/تصادف/خطر و ...
#
# حالت کم‌مصرف فعلی:
# 6 شهر بزرگ: ترافیک هر 120 دقیقه، alerts هر 720 دقیقه (12 ساعت)
# 9 شهر دیگر: ترافیک هر 360 دقیقه (6 ساعت)، alerts هر 1440 دقیقه (24 ساعت)
# Workflow همچنان هر 10 دقیقه اجرا می‌شود.
# ============================================================
REGIONS = {
    "tehran": {"name": "تهران", "bottom_left": "35.45,51.05", "top_right": "35.90,51.65", "jams_interval_min": 120, "alerts_interval_min": 720},
    "mashhad": {"name": "مشهد", "bottom_left": "36.15,59.40", "top_right": "36.45,59.80", "jams_interval_min": 120, "alerts_interval_min": 720},
    "karaj": {"name": "کرج", "bottom_left": "35.70,50.80", "top_right": "35.95,51.20", "jams_interval_min": 120, "alerts_interval_min": 720},
    "isfahan": {"name": "اصفهان", "bottom_left": "32.50,51.50", "top_right": "32.80,51.85", "jams_interval_min": 120, "alerts_interval_min": 720},
    "shiraz": {"name": "شیراز", "bottom_left": "29.45,52.35", "top_right": "29.75,52.70", "jams_interval_min": 120, "alerts_interval_min": 720},
    "tabriz": {"name": "تبریز", "bottom_left": "37.95,46.10", "top_right": "38.20,46.45", "jams_interval_min": 120, "alerts_interval_min": 720},
    "ahvaz": {"name": "اهواز", "bottom_left": "31.20,48.55", "top_right": "31.45,48.85", "jams_interval_min": 360, "alerts_interval_min": 1440},
    "qom": {"name": "قم", "bottom_left": "34.50,50.70", "top_right": "34.75,51.05", "jams_interval_min": 360, "alerts_interval_min": 1440},
    "rasht": {"name": "رشت", "bottom_left": "37.15,49.45", "top_right": "37.40,49.75", "jams_interval_min": 360, "alerts_interval_min": 1440},
    "kermanshah": {"name": "کرمانشاه", "bottom_left": "34.20,46.90", "top_right": "34.45,47.25", "jams_interval_min": 360, "alerts_interval_min": 1440},
    "urmia": {"name": "ارومیه", "bottom_left": "37.40,44.90", "top_right": "37.70,45.25", "jams_interval_min": 360, "alerts_interval_min": 1440},
    "kerman": {"name": "کرمان", "bottom_left": "30.15,56.90", "top_right": "30.40,57.25", "jams_interval_min": 360, "alerts_interval_min": 1440},
    "yazd": {"name": "یزد", "bottom_left": "31.75,54.20", "top_right": "32.00,54.55", "jams_interval_min": 360, "alerts_interval_min": 1440},
    "bandar_abbas": {"name": "بندرعباس", "bottom_left": "27.05,56.10", "top_right": "27.30,56.45", "jams_interval_min": 360, "alerts_interval_min": 1440},
    "zahedan": {"name": "زاهدان", "bottom_left": "29.35,60.70", "top_right": "29.65,61.05", "jams_interval_min": 360, "alerts_interval_min": 1440},
}

TRAFFIC_DIR = Path("traffic")
STATE_FILE = Path("key_state.json")
BASE_URL = "https://api.wazeapi.com/v1"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return now_utc().isoformat().replace("+00:00", "Z")


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def due(last_value: Optional[str], interval_min: int) -> bool:
    last = parse_iso(last_value)
    if last is None:
        return True
    return (now_utc() - last).total_seconds() >= interval_min * 60


def load_keys() -> list[str]:
    raw = os.environ.get("WAZE_API_KEYS", "").strip()
    if not raw:
        print("⚠️ WAZE_API_KEYS تنظیم نشده است.")
        return []
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    print(f"🔑 تعداد کلیدهای بارگذاری‌شده: {len(keys)}")
    return keys


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"current_index": 0, "failed_keys": []}


def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_next_key(keys: list[str], state: dict) -> Optional[str]:
    if not keys:
        return None
    n = len(keys)
    start = state.get("current_index", 0) % n
    failed = set(state.get("failed_keys", []))
    for i in range(n):
        idx = (start + i) % n
        key = keys[idx]
        if key not in failed:
            state["current_index"] = idx
            return key
    state["failed_keys"] = []
    state["current_index"] = 0
    return keys[0]


def mark_key_failed(state: dict, key: str, key_count: int):
    failed = state.get("failed_keys", [])
    if key not in failed:
        failed.append(key)
    state["failed_keys"] = failed
    if key_count:
        state["current_index"] = (state.get("current_index", 0) + 1) % key_count


def call_waze(endpoint: str, params: dict, api_key: str) -> tuple[Optional[Any], bool]:
    url = f"{BASE_URL}/{endpoint}"
    headers = {"X-API-Key": api_key, "Accept": "application/json"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=45)
        if resp.status_code == 200:
            try:
                return resp.json(), False
            except Exception as e:
                print(f"   ⚠️ JSON parse error: {e}")
                return None, False
        if resp.status_code in (401, 403, 429):
            print(f"   ❌ کلید/سهمیه مشکل دارد (status={resp.status_code})")
            return None, True
        print(f"   ⚠️ پاسخ غیرمنتظره: {resp.status_code} - {resp.text[:300]}")
        return None, False
    except Exception as e:
        print(f"   ⚠️ خطا در درخواست: {e}")
        return None, False


def extract_alerts(data: Any) -> list:
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("alerts"), list):
            return data["alerts"]
        if isinstance(data.get("data"), dict) and isinstance(data["data"].get("alerts"), list):
            return data["data"]["alerts"]
        if isinstance(data.get("data"), list):
            return data["data"]
    return []


def extract_jams(data: Any) -> list:
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("jams"), list):
            return data["jams"]
        if isinstance(data.get("data"), dict) and isinstance(data["data"].get("jams"), list):
            return data["data"]["jams"]
        if isinstance(data.get("data"), list):
            return data["data"]
    return []


def load_region_file(region_id: str, region: dict) -> dict:
    path = TRAFFIC_DIR / f"{region_id}.json"
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {
        "region": region_id,
        "name": region["name"],
        "status": "error",
        "alerts": [],
        "jams": [],
        "meta": {},
        "schedule": {"last_alerts_update": None, "last_jams_update": None},
    }


def request_with_rotation(endpoint: str, params: dict, keys: list[str], state: dict) -> Optional[Any]:
    if not keys:
        return None
    attempted = set()
    while len(attempted) < len(keys):
        key = get_next_key(keys, state)
        if not key or key in attempted:
            break
        attempted.add(key)
        print(f"    → {endpoint} با کلید ...{key[-8:]}")
        data, key_error = call_waze(endpoint, params, key)
        if data is not None:
            save_state(state)
            return data
        if key_error:
            mark_key_failed(state, key, len(keys))
        else:
            break
    save_state(state)
    return None


def fetch_region(region_id: str, region: dict, keys: list[str], state: dict) -> tuple[dict, bool, int]:
    result = load_region_file(region_id, region)
    schedule = result.setdefault("schedule", {})
    params = {"bottom-left": region["bottom_left"], "top-right": region["top_right"]}
    changed = False
    request_count = 0

    jams_due = due(schedule.get("last_jams_update"), region["jams_interval_min"])
    alerts_due = due(schedule.get("last_alerts_update"), region["alerts_interval_min"])
    print(f"  ⏱ jams={'نیاز دارد' if jams_due else 'هنوز معتبر'} | alerts={'نیاز دارد' if alerts_due else 'هنوز معتبر'}")

    if not jams_due and not alerts_due:
        return result, False, 0

    if jams_due:
        data = request_with_rotation("alerts/jams", params, keys, state)
        request_count += 1 if data is not None else 0
        if data is not None:
            result["jams"] = extract_jams(data)
            schedule["last_jams_update"] = iso_now()
            changed = True
            print(f"  ✅ jams: {len(result['jams'])}")
        else:
            print("  ⚠️ دریافت jams ناموفق بود؛ timestamp قبلی حفظ شد.")

    if alerts_due:
        data = request_with_rotation("alerts", params, keys, state)
        request_count += 1 if data is not None else 0
        if data is not None:
            result["alerts"] = extract_alerts(data)
            schedule["last_alerts_update"] = iso_now()
            changed = True
            print(f"  ✅ alerts: {len(result['alerts'])}")
        else:
            print("  ⚠️ دریافت alerts ناموفق بود؛ timestamp قبلی حفظ شد.")

    if changed:
        result["region"] = region_id
        result["name"] = region["name"]
        result["status"] = "ok"
        result["updated_at"] = iso_now()
        result["meta"] = {
            "alerts_count": len(result.get("alerts", [])),
            "jams_count": len(result.get("jams", [])),
            "jams_interval_min": region["jams_interval_min"],
            "alerts_interval_min": region["alerts_interval_min"],
        }
    return result, changed, request_count


def write_json_if_changed(path: Path, data: dict) -> bool:
    new_text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    old_text = path.read_text(encoding="utf-8") if path.exists() else None
    if old_text == new_text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def build_summary() -> dict:
    summary = {
        "updated_at": iso_now(),
        "regions": {},
        "total_alerts": 0,
        "total_jams": 0,
    }
    for region_id, region in REGIONS.items():
        data = load_region_file(region_id, region)
        summary["regions"][region_id] = {
            "name": region["name"],
            "status": data.get("status", "error"),
            "alerts": len(data.get("alerts", [])),
            "jams": len(data.get("jams", [])),
            "updated_at": data.get("updated_at"),
            "last_alerts_update": data.get("schedule", {}).get("last_alerts_update"),
            "last_jams_update": data.get("schedule", {}).get("last_jams_update"),
        }
        summary["total_alerts"] += len(data.get("alerts", []))
        summary["total_jams"] += len(data.get("jams", []))
    return summary


def main():
    print("=" * 60)
    print("Iran Traffic Data — WazeAPI + Aggressive Scheduler/TTL")
    print("Workflow هر ۱۰ دقیقه اجرا می‌شود؛ فقط مناطق due درخواست می‌شوند.")
    print("=" * 60)

    keys = load_keys()
    state = load_state()
    TRAFFIC_DIR.mkdir(exist_ok=True)

    any_changed = False
    total_requests = 0

    for region_id, region in REGIONS.items():
        print(f"\n📍 {region['name']} ({region_id})")
        data, changed, requests_used = fetch_region(region_id, region, keys, state)
        total_requests += requests_used
        if changed:
            path = TRAFFIC_DIR / f"{region_id}.json"
            if write_json_if_changed(path, data):
                any_changed = True
        if requests_used:
            time.sleep(1.0)

    if any_changed:
        summary = build_summary()
        write_json_if_changed(TRAFFIC_DIR / "summary.json", summary)
    else:
        print("\nℹ️ هیچ TTL منقضی نشده یا هیچ درخواست موفقی انجام نشد؛ summary.json تغییر نمی‌کند.")

    save_state(state)
    print("\n" + "=" * 60)
    print(f"تعداد درخواست‌های موفق این اجرا: {total_requests}")
    print(f"تغییر داده‌ها: {'بله' if any_changed else 'خیر'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
