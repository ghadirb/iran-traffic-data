#!/usr/bin/env python3
"""
اسکریپت به‌روزرسانی داده‌های ترافیک، پلیس، تصادف و حوادث از WazeAPI

- از چند کلید API پشتیبانی می‌کند (چرخشی و ترتیبی)
- هر ۱۰ دقیقه توسط GitHub Actions اجرا می‌شود
- خروجی: فایل‌های JSON در پوشه traffic/
"""

import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

import requests

# ============================================================
# تنظیمات مناطق (bounding box تقریبی اطراف شهرهای اصلی)
# bottom-left = lat_min,lng_min   |   top-right = lat_max,lng_max
# ============================================================
REGIONS = {
    "tehran": {
        "name": "تهران",
        "bottom_left": "35.45,51.05",
        "top_right": "35.90,51.65",
    },
    "karaj": {
        "name": "کرج",
        "bottom_left": "35.70,50.80",
        "top_right": "35.95,51.20",
    },
    "isfahan": {
        "name": "اصفهان",
        "bottom_left": "32.50,51.50",
        "top_right": "32.80,51.85",
    },
    "mashhad": {
        "name": "مشهد",
        "bottom_left": "36.15,59.40",
        "top_right": "36.45,59.80",
    },
    "shiraz": {
        "name": "شیراز",
        "bottom_left": "29.45,52.35",
        "top_right": "29.75,52.70",
    },
    "tabriz": {
        "name": "تبریز",
        "bottom_left": "37.95,46.10",
        "top_right": "38.20,46.45",
    },
    "ahvaz": {
        "name": "اهواز",
        "bottom_left": "31.20,48.55",
        "top_right": "31.45,48.85",
    },
    "qom": {
        "name": "قم",
        "bottom_left": "34.50,50.70",
        "top_right": "34.75,51.05",
    },
    "rasht": {
        "name": "رشت",
        "bottom_left": "37.15,49.45",
        "top_right": "37.40,49.75",
    },
    "kermanshah": {
        "name": "کرمانشاه",
        "bottom_left": "34.20,46.90",
        "top_right": "34.45,47.25",
    },
    "urmia": {
        "name": "ارومیه",
        "bottom_left": "37.40,44.90",
        "top_right": "37.70,45.25",
    },
    "kerman": {
        "name": "کرمان",
        "bottom_left": "30.15,56.90",
        "top_right": "30.40,57.25",
    },
    "yazd": {
        "name": "یزد",
        "bottom_left": "31.75,54.20",
        "top_right": "32.00,54.55",
    },
    "bandar_abbas": {
        "name": "بندرعباس",
        "bottom_left": "27.05,56.10",
        "top_right": "27.30,56.45",
    },
    "zahedan": {
        "name": "زاهدان",
        "bottom_left": "29.35,60.70",
        "top_right": "29.65,61.05",
    },
}

TRAFFIC_DIR = Path("traffic")
STATE_FILE = Path("key_state.json")
BASE_URL = "https://api.wazeapi.com/v1"


def load_keys() -> list[str]:
    """کلیدها را از متغیر محیطی می‌خواند (جدا شده با کاما)"""
    raw = os.environ.get("WAZE_API_KEYS", "").strip()
    if not raw:
        print("⚠️  WAZE_API_KEYS تنظیم نشده است.")
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
    """کلید بعدی سالم را برمی‌گرداند (چرخشی)"""
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

    # همه کلیدها fail شده‌اند → لیست failed را پاک کن و از اول شروع کن
    print("🔄 همه کلیدها fail شده بودند. ریست و شروع دوباره...")
    state["failed_keys"] = []
    state["current_index"] = 0
    return keys[0] if keys else None


def mark_key_failed(state: dict, key: str):
    failed = state.get("failed_keys", [])
    if key not in failed:
        failed.append(key)
        state["failed_keys"] = failed
    # به کلید بعدی برو
    state["current_index"] = (state.get("current_index", 0) + 1) % max(len(failed) + 1, 1)


def call_waze(endpoint: str, params: dict, api_key: str) -> Optional[Any]:
    """یک درخواست به WazeAPI می‌زند. ممکن است dict یا list برگرداند."""
    url = f"{BASE_URL}/{endpoint}"
    headers = {"X-API-Key": api_key, "Accept": "application/json"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=45)
        if resp.status_code == 200:
            try:
                return resp.json()
            except Exception as e:
                print(f"   ⚠️  JSON parse error: {e}")
                return None
        if resp.status_code in (401, 403, 429):
            print(f"   ❌ کلید مشکل دارد (status={resp.status_code})")
            return None  # یعنی کلید را fail کن
        print(f"   ⚠️  پاسخ غیرمنتظره: {resp.status_code} - {resp.text[:300]}")
        return None
    except Exception as e:
        print(f"   ⚠️  خطا در درخواست: {e}")
        return None


def extract_alerts(data: Any) -> list:
    """از پاسخ API (dict یا list) لیست alerts را استخراج می‌کند."""
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # فرمت‌های رایج: {"alerts": [...]}, {"data": {"alerts": [...]}}, {"count": N, "alerts": [...]}
        if "alerts" in data and isinstance(data["alerts"], list):
            return data["alerts"]
        if "data" in data and isinstance(data["data"], dict):
            inner = data["data"]
            if "alerts" in inner and isinstance(inner["alerts"], list):
                return inner["alerts"]
        # گاهی خود data لیست است
        if "data" in data and isinstance(data["data"], list):
            return data["data"]
    return []


def extract_jams(data: Any, fallback_alerts_data: Any = None) -> list:
    """از پاسخ API لیست jams را استخراج می‌کند."""
    if data is None:
        data = {}
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "jams" in data and isinstance(data["jams"], list):
            return data["jams"]
        if "data" in data and isinstance(data["data"], dict):
            inner = data["data"]
            if "jams" in inner and isinstance(inner["jams"], list):
                return inner["jams"]
        if "data" in data and isinstance(data["data"], list):
            return data["data"]
    # fallback: ممکن است jams داخل پاسخ alerts باشد
    if fallback_alerts_data and isinstance(fallback_alerts_data, dict):
        if "jams" in fallback_alerts_data and isinstance(fallback_alerts_data["jams"], list):
            return fallback_alerts_data["jams"]
    return []


def fetch_region(region_id: str, region: dict, keys: list[str], state: dict) -> dict:
    """داده‌های alerts و jams یک منطقه را می‌گیرد"""
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    result = {
        "region": region_id,
        "name": region["name"],
        "updated_at": now,
        "status": "error",
        "alerts": [],
        "jams": [],
        "meta": {},
    }

    if not keys:
        result["message"] = "هیچ کلید API تنظیم نشده"
        return result

    params = {
        "bottom-left": region["bottom_left"],
        "top-right": region["top_right"],
    }

    # حداکثر ۳ بار تلاش با کلیدهای مختلف
    for attempt in range(min(3, len(keys))):
        key = get_next_key(keys, state)
        if not key:
            break

        print(f"  → تلاش با کلید ...{key[-8:]} (attempt {attempt+1})")

        alerts_data = call_waze("alerts", params, key)
        if alerts_data is None:
            mark_key_failed(state, key)
            continue

        # jams (اگر endpoint جدا باشد)
        jams_data = call_waze("alerts/jams", params, key)
        # اگر jams جدا کار نکرد، ممکن است داخل alerts باشد یا endpoint دیگری

        # استخراج داده (مقاوم در برابر list یا dict)
        alerts = extract_alerts(alerts_data)
        jams = extract_jams(jams_data, fallback_alerts_data=alerts_data)

        result["alerts"] = alerts
        result["jams"] = jams
        result["status"] = "ok"
        result["meta"] = {
            "alerts_count": len(alerts),
            "jams_count": len(jams),
            "key_used_suffix": key[-8:],
            "alerts_response_type": type(alerts_data).__name__,
        }
        print(f"  ✅ موفق: {len(alerts)} alert، {len(jams)} jam")
        # این کلید خوب بود → ایندکس را نگه دار
        save_state(state)
        return result

    result["message"] = "همه تلاش‌ها با کلیدها ناموفق بود"
    save_state(state)
    return result


def main():
    print("=" * 50)
    print("شروع به‌روزرسانی داده‌های ترافیک ایران از WazeAPI")
    print("=" * 50)

    keys = load_keys()
    state = load_state()
    TRAFFIC_DIR.mkdir(exist_ok=True)

    summary = {
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "regions": {},
        "total_alerts": 0,
        "total_jams": 0,
    }

    for region_id, region in REGIONS.items():
        print(f"\n📍 در حال دریافت داده برای: {region['name']} ({region_id})")
        data = fetch_region(region_id, region, keys, state)

        file_path = TRAFFIC_DIR / f"{region_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        summary["regions"][region_id] = {
            "status": data["status"],
            "alerts": data.get("meta", {}).get("alerts_count", 0),
            "jams": data.get("meta", {}).get("jams_count", 0),
        }
        summary["total_alerts"] += data.get("meta", {}).get("alerts_count", 0)
        summary["total_jams"] += data.get("meta", {}).get("jams_count", 0)

        # کمی فاصله بین درخواست‌ها تا rate-limit نخوریم
        time.sleep(1.5)

    # فایل خلاصه کل ایران
    with open(TRAFFIC_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    save_state(state)
    print("\n" + "=" * 50)
    print(f"تمام شد. مجموع alerts: {summary['total_alerts']} | jams: {summary['total_jams']}")
    print("=" * 50)


if __name__ == "__main__":
    main()
