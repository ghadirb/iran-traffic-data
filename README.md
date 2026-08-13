# Iran Traffic Data (WazeAPI)

این ریپازیتوری داده‌های **ترافیک، پلیس، تصادف، خطر و حوادث جاده‌ای** ایران را از WazeAPI دریافت و در فایل‌های JSON ذخیره می‌کند.

برنامه اندروید فقط فایل‌های JSON را می‌خواند و نیازی به مدیریت کلید API ندارد.

## زمان‌بندی و کاهش مصرف API

Workflow همچنان **هر ۱۰ دقیقه** اجرا می‌شود، اما این به معنی یک درخواست WazeAPI در هر اجرا یا درخواست برای همه شهرها نیست.

اسکریپت برای هر شهر/منطقه TTL جداگانه دارد و فقط وقتی TTL منقضی شده باشد endpoint مربوطه را صدا می‌زند:

- شهرهای بزرگ: `jams` هر ۳۰ دقیقه، `alerts` هر ۲ ساعت
- شهرهای دیگر: `jams` هر ۶۰ دقیقه، `alerts` هر ۴ ساعت

بنابراین ممکن است Workflow هر ۱۰ دقیقه اجرا شود ولی در بسیاری از اجراها **هیچ درخواست WazeAPI** انجام نشود.

### نکته مهم درباره مصرف

اجرای GitHub Actions، ساخت JSON، commit و push به‌خودی‌خود درخواست WazeAPI نیستند. فقط درخواست‌های HTTP به WazeAPI مصرف API ایجاد می‌کنند.

در اولین اجرای بعد از نصب/پاک شدن فایل‌های شهرها، همه شهرها به‌دلیل نداشتن timestamp قبلی نیازمند دریافت هستند. بعد از آن Scheduler بر اساس TTL کار می‌کند.

اگر یک درخواست ناموفق باشد، timestamp قبلی آن endpoint تغییر نمی‌کند تا در اجرای بعدی دوباره امتحان شود.

## ساختار خروجی

```
traffic/
├── tehran.json
├── karaj.json
├── isfahan.json
├── mashhad.json
├── shiraz.json
├── tabriz.json
├── ahvaz.json
├── qom.json
├── rasht.json
├── kermanshah.json
├── urmia.json
├── kerman.json
├── yazd.json
├── bandar_abbas.json
├── zahedan.json
└── summary.json
```

هر فایل شهر شامل موارد اصلی زیر است:

- `alerts` → پلیس، تصادف، خطر، بسته بودن جاده و ...
- `jams` → ترافیک‌های فعال
- `updated_at` → آخرین تغییر موفق فایل
- `schedule.last_alerts_update` → آخرین دریافت موفق alerts
- `schedule.last_jams_update` → آخرین دریافت موفق jams
- `status` → `ok` یا `error`

`summary.json` آخرین وضعیت همه شهرها و زمان آخرین به‌روزرسانی هر نوع داده را خلاصه می‌کند.

## لینک فایل‌ها

```
https://raw.githubusercontent.com/ghadirb/iran-traffic-data/main/traffic/summary.json
https://raw.githubusercontent.com/ghadirb/iran-traffic-data/main/traffic/tehran.json
```

## کلیدهای WazeAPI

کلیدها را در GitHub به‌عنوان Secret قرار دهید:

**Settings → Secrets and variables → Actions → New repository secret**

نام Secret:

`WAZE_API_KEYS`

اگر چند credential مجاز دارید، می‌توانید آنها را با کاما جدا کنید:

```
wz_live_xxxx1,wz_live_xxxx2,wz_live_xxxx3
```

کلیدها در کد یا فایل JSON عمومی ذخیره نمی‌شوند. از چند کلید فقط در چارچوب مجاز سرویس و شرایط حساب‌های مربوطه استفاده کنید؛ این سیستم برای مدیریت credential و ادامه کار در صورت خطای یک کلید است، نه برای دور زدن محدودیت یک پلن.

## زمان‌بندی Workflow

فایل `.github/workflows/update-traffic.yml` هر **۱۰ دقیقه** اجرا می‌شود و اجرای دستی (`workflow_dispatch`) نیز فعال است.

حتی در اجرای دستی، TTL رعایت می‌شود؛ بنابراین اجرای دستی هم لزوماً برای همه شهرها درخواست API نمی‌زند.

## افزودن شهر یا تغییر TTL

در `scripts/update_traffic.py` برای هر منطقه این مقادیر قابل تغییر هستند:

```python
"jams_interval_min": 30,
"alerts_interval_min": 120,
```

مثلاً برای یک شهر مهم‌تر می‌توان `jams_interval_min` را به 20 کاهش داد، یا برای کاهش بیشتر مصرف آن را به 60 افزایش داد.

## نکته برای اپ همراه راننده

برنامه بهتر است ابتدا `summary.json` را بخواند تا بفهمد داده هر شهر چه زمانی به‌روزرسانی شده است و سپس فقط فایل شهر موردنیاز را دریافت کند. این کار **هیچ مصرف WazeAPI** ایجاد نمی‌کند، چون اپ مستقیماً WazeAPI را صدا نمی‌زند.
