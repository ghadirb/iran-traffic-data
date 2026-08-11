# Iran Traffic Data

این ریپازیتوری داده‌های ترافیک استان‌های ایران را به صورت خودکار به‌روزرسانی می‌کند.

## ساختار فایل‌ها

```
traffic/
├── tehran.json
├── isfahan.json
├── mashhad.json
├── shiraz.json
├── tabriz.json
├── karaj.json
├── ahvaz.json
├── qom.json
└── rasht.json
```

## لینک‌های مستقیم (بعد از عمومی کردن ریپو)

```
https://raw.githubusercontent.com/ghadirb/iran-traffic-data/main/traffic/tehran.json
https://raw.githubusercontent.com/ghadirb/iran-traffic-data/main/traffic/isfahan.json
...
```

> **توجه:** تا زمانی که ریپو خصوصی است، این لینک‌ها بدون احراز هویت کار نمی‌کنند.

## نحوه افزودن کلید پارسی‌مپ

1. به صفحه ریپو برو: https://github.com/ghadirb/iran-traffic-data
2. برو به **Settings** → **Secrets and variables** → **Actions**
3. روی **New repository secret** کلیک کن
4. Name را بنویس: `PARSIMAP_API_KEY`
5. Value را کلید API پارسی‌مپ خودت بگذار
6. ذخیره کن

بعد از اضافه کردن کلید، workflow به صورت خودکار شروع به گرفتن داده واقعی می‌کند.

## زمان‌بندی

Workflow هر ۱۰ دقیقه یک‌بار اجرا می‌شود (قابل تغییر در فایل `.github/workflows/update-traffic.yml`).
