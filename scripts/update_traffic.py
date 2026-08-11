#!/usr/bin/env python3
"""
اسکریپت به‌روزرسانی داده‌های ترافیک از پارسی‌مپ

توجه:
- این اسکریپت فعلاً ساختار پایه دارد.
- بعد از اضافه کردن کلید PARSIMAP_API_KEY در Secrets،
  بخش مربوط به فراخوانی API را کامل کن.
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path

# لیست استان‌ها / شهرهای اصلی
PROVINCES = [
    "tehran",
    "isfahan",
    "mashhad",
    "shiraz",
    "tabriz",
    "karaj",
    "ahvaz",
    "qom",
    "rasht",
]

TRAFFIC_DIR = Path("traffic")


def get_api_key():
    key = os.environ.get("PARSIMAP_API_KEY")
    if not key:
        print("⚠️  PARSIMAP_API_KEY پیدا نشد. از داده نمونه استفاده می‌شود.")
        return None
    return key


def fetch_traffic_for_province(province: str, api_key: str | None):
    """
    اینجا باید درخواست واقعی به پارسی‌مپ زده شود.

    مثال (باید با مستندات رسمی پارسی‌مپ تطبیق داده شود):

    import requests
    url = "https://api.parsimap.ir/..."  # آدرس واقعی سرویس ترافیک/مسیریابی
    headers = {"Api-Key": api_key}  # یا هدر مورد نیاز پارسی‌مپ
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()
    """

    # فعلاً داده نمونه برمی‌گردانیم تا ساختار کار کند
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if api_key is None:
        return {
            "province": province,
            "updated_at": now,
            "status": "placeholder",
            "message": "کلید API تنظیم نشده است",
            "routes": [],
        }

    # TODO: بعد از داشتن کلید و مستندات دقیق، این بخش را کامل کن
    return {
        "province": province,
        "updated_at": now,
        "status": "ready_for_api",
        "message": "کلید موجود است اما فراخوانی واقعی API هنوز پیاده‌سازی نشده",
        "routes": [],
    }


def main():
    api_key = get_api_key()
    TRAFFIC_DIR.mkdir(exist_ok=True)

    for province in PROVINCES:
        print(f"Updating {province}...")
        data = fetch_traffic_for_province(province, api_key)

        file_path = TRAFFIC_DIR / f"{province}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  → {file_path} updated")

    print("Done.")


if __name__ == "__main__":
    main()
