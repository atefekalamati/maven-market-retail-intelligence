# راهنمای دموی زنده با SQL Server

این راهنما برای اجرای زندهٔ کوئری‌های پروژه در SQL Server Management Studio (SSMS) است.

| مورد | مقدار |
|---|---|
| Server name | `localhost\SQLEXPRESS` |
| Authentication | Windows Authentication |
| Database | `MavenMarketDW` |
| Schema | `analytics` |

فایل‌ها به ترتیب:

1. `01_create_star_schema.sql`: ساخت جدول‌های ستاره‌ای (خالی)
2. `02_analytical_queries.sql`: ده کوئری تحلیلی Q1 تا Q10 با نتیجهٔ مورد انتظار در کامنت
3. `03_practice_queries.sql`: شانزده کوئری تمرینی P1 تا P16

بارگذاری داده (فقط یک بار لازم است، از ریشهٔ پروژه):

```powershell
python scripts/load_sql_server.py --data-dir E:\SQLData
```

این اسکریپت دیتابیس را می‌سازد (فایل‌های `.mdf` و `.ldf` در `E:\SQLData`)، فایل `01` را اجرا می‌کند،
اول Dimensionها و بعد Factها را بارگذاری می‌کند و تعداد ردیف‌ها و جمع Revenue و Profit را چک می‌کند.
نتیجهٔ اجرای همهٔ کوئری‌ها در `reports/sql_query_validation.md` است.

## ۱. باز کردن SSMS و اتصال

1. منوی Start را باز کن و `SQL Server Management Studio` را تایپ و اجرا کن.
2. پنجرهٔ **Connect to Server** خودش باز می‌شود. اگر باز نشد: **File → Connect Object Explorer**.
3. این‌ها را پر کن:
   - **Server type:** `Database Engine`
   - **Server name:** `localhost\SQLEXPRESS`
   - **Authentication:** `Windows Authentication` (نام کاربری و رمز لازم نیست)
   - **Encryption:** `Mandatory` بماند، ولی تیک **Trust server certificate** را حتماً بزن.
     بدون این تیک خطای گواهی (certificate chain) می‌گیری.
4. روی **Connect** بزن.
5. در **Object Explorer** سمت چپ: `Databases → MavenMarketDW → Tables` و جدول‌های `analytics.*` را نشان بده.

## ۲. اجرای یک کوئری انتخاب‌شده (F5)

1. **File → Open → File...** (یا `Ctrl+O`) و فایل `02_analytical_queries.sql` را باز کن.
2. در نوار ابزار بالا، از لیست کشویی دیتابیس، `MavenMarketDW` را انتخاب کن
   (یا اول فایل یک بار `USE MavenMarketDW;` را اجرا کن).
3. فقط متن یک کوئری را با ماوس انتخاب کن (مثلاً از `WITH yearly AS` تا `ORDER BY [year];` در Q1).
4. **F5** را بزن (یا دکمهٔ **Execute**).
   - اگر چیزی انتخاب نشده باشد، F5 **کل فایل** را اجرا می‌کند؛ پس همیشه اول انتخاب کن.
5. نتیجه در تب **Results** پایین صفحه می‌آید و تعداد ردیف‌ها و زمان در نوار وضعیت پایین راست دیده می‌شود.

نکته: Q10 یک View و یک Index می‌سازد. View با `CREATE OR ALTER` است و دوباره اجرا شدنش مشکلی ندارد؛
ولی `CREATE INDEX` اگر Index از قبل باشد خطا می‌دهد. پس در دمو فقط View را اجرا کن، یا اگر Index را
می‌خواهی دوباره بسازی اول این را اجرا کن:

```sql
DROP INDEX IF EXISTS IX_FactSales_Date_Store_Covering ON analytics.FactSales;
```

## ۳. نمایش Actual Execution Plan (Ctrl+M)

1. قبل از اجرا **Ctrl+M** را بزن (یا **Query → Include Actual Execution Plan**).
   دکمه‌اش در نوار ابزار حالت فعال (فرورفته) می‌گیرد.
2. کوئری را انتخاب کن و **F5** بزن.
3. کنار تب Results یک تب جدید به نام **Execution plan** می‌آید.
4. پلن از **راست به چپ** خوانده می‌شود. چیزهایی که در مصاحبه می‌شود نشان داد:
   - **Clustered Index Scan** در برابر **Index Seek**
   - **Hash Match** برای JOIN و GROUP BY روی جدول بزرگ (FactSales با ۲۶۹,۷۲۰ ردیف)
   - درصد **Cost** هر عملگر؛ پرهزینه‌ترین بخش را پیدا کن.
   - ماوس را روی هر عملگر نگه دار تا **Actual Number of Rows** و **Estimated Number of Rows** را ببینی.
5. برای خاموش کردن، دوباره **Ctrl+M** بزن.

پیشنهاد دمو: پلن Q10 را یک بار قبل و یک بار بعد از ساخت Index پوششی
`IX_FactSales_Date_Store_Covering` مقایسه کن.

## ۴. دیدن زمان و I/O (SET STATISTICS IO, TIME ON)

1. این خط را بالای کوئری بنویس و همراه کوئری انتخاب و اجرا کن:

   ```sql
   SET STATISTICS IO, TIME ON;
   ```

2. بعد از اجرا به تب **Messages** (کنار Results) برو. آنجا می‌بینی:
   - **logical reads** برای هر جدول: تعداد صفحه‌های ۸ کیلوبایتی که خوانده شده (معیار اصلی هزینه)
   - **CPU time** و **elapsed time** بر حسب میلی‌ثانیه
3. برای خاموش کردن:

   ```sql
   SET STATISTICS IO, TIME OFF;
   ```

نکته: اجرای اول ممکن است کندتر باشد چون داده هنوز در حافظه (buffer cache) نیست؛
برای مقایسهٔ منصفانه هر کوئری را دو بار اجرا کن و عدد بار دوم را ببین.

## اگر اتصال برقرار نشد

- سرویس را بررسی کن: در PowerShell `Get-Service 'MSSQL$SQLEXPRESS'`؛ اگر `Stopped` بود، با دسترسی ادمین `Start-Service 'MSSQL$SQLEXPRESS'`.
- Server name را دقیقاً با بک‌اسلش بنویس: `localhost\SQLEXPRESS` (یا `.\SQLEXPRESS`).
- خطای certificate: تیک **Trust server certificate** را بزن.
