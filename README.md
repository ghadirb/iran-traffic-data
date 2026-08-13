# Iran Traffic Data (WazeAPI)

این ریپازیتوری داده‌های **زنده ترافیک، پلیس، تصادف، خطر و حوادث جاده‌ای** ایران را هر ۱۰ دقیقه از [WazeAPI](https://wazeapi.com) دریافت و در فایل‌های JSON ذخیره می‌کند.

برنامه اندروید شما فقط این فایل‌های JSON را می‌خواند و نیازی به مدیریت کلید API ندارد.

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
└── summary.json          ← خلاصه وضعیت همه شهرها
```

هر فایل شامل فیلدهای اصلی زیر است:

- `alerts` → لیست پلیس، تصادف، خطر، بسته بودن جاده و ...
- `jams` → ترافیک‌های فعال (سرعت، تأخیر، مسیر)
- `updated_at` → زمان آخرین به‌روزرسانی (UTC)
- `status` → `ok` یا `error`

## لینک مستقیم فایل‌ها (بعد از عمومی کردن ریپو)

```
https://raw.githubusercontent.com/ghadirb/iran-traffic-data/main/traffic/tehran.json
https://raw.githubusercontent.com/ghadirb/iran-traffic-data/main/traffic/summary.json
...
```

> **توجه:** تا وقتی ریپو خصوصی است، برای دسترسی به raw فایل‌ها نیاز به توکن دارید.

## نحوه افزودن کلیدهای WazeAPI (هر تعداد که بخواهید)

1. به صفحه ریپو بروید: https://github.com/ghadirb/iran-traffic-data
2. بروید به **Settings** → **Secrets and variables** → **Actions**
3. روی **New repository secret** کلیک کنید
4. **Name** را بنویسید: `WAZE_API_KEYS`
5. **Value** را کلیدها را با کاما از هم جدا کنید، مثال:

   ```
   wz_live_xxxx1,wz_live_xxxx2,wz_live_xxxx3,wz_live_xxxx4
   ```

6. ذخیره کنید.

اسکریپت به صورت خودکار:
- کلیدها را **به ترتیب** استفاده می‌کند
- اگر کلیدی تمام شد یا خطا داد → به کلید بعدی می‌رود
- وقتی به آخر لیست رسید → دوباره از اول شروع می‌کند
- وضعیت کلیدها را در فایل `key_state.json` نگه می‌دارد

## زمان‌بندی

Workflow هر **۱۰ دقیقه** یک‌بار اجرا می‌شود (قابل تغییر در `.github/workflows/update-traffic.yml`).

می‌توانید از تب **Actions** نیز به صورت دستی اجرا کنید (workflow_dispatch).

## افزودن شهر یا منطقه جدید

در فایل `scripts/update_traffic.py` دیکشنری `REGIONS` را ویرایش کنید و bounding box مناسب اضافه کنید.

## نکات مهم

- پلن رایگان WazeAPI فقط ۱۰۰ درخواست در ماه دارد. با چند کلید و چرخش می‌توانید محدودیت را دور بزنید (البته شرایط استفاده سرویس را رعایت کنید).
- اگر ریپو برای مدت طولانی بدون فعالیت بماند، GitHub ممکن است schedule را موقتاً متوقف کند. یک commit ساده دوباره فعالش می‌کند.
- داده‌ها live هستند و دقیقاً همان چیزی است که رانندگان Waze می‌بینند.
