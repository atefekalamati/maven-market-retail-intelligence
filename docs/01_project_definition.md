# Maven Market Executive Retail Intelligence

<div dir="rtl" align="right">

**مرحله:** ۱ — تعریف سناریوی کسب‌وکار و Project Brief  
**وضعیت:** تکمیل‌شده  
**نقش پروژه:** Junior Data Analyst & Business Intelligence Developer  
**آخرین به‌روزرسانی:** ۲۶ ژوئیه ۲۰۲۶

---

## ۱. عنوان حرفه‌ای پروژه

### عنوان فارسی

**هوشمندی مدیریتی خرده‌فروشی Maven Market: تحلیل عملکرد فروش، ارزش مشتری و سودآوری**

### عنوان انگلیسی

**Maven Market Executive Retail Intelligence: Sales, Customer Value & Profitability Analytics**

### عنوان کوتاه پروژه

**Maven Market Retail Intelligence**

### نام مخزن GitHub

`maven-market-retail-intelligence`

---

## ۲. معرفی شرکت فرضی

### نام شرکت

**Maven Market Group**

### صنعت

خرده‌فروشی مواد غذایی و کالاهای مصرفی  
**Grocery and Consumer Retail**

### محدوده فعالیت

Maven Market یک زنجیره خرده‌فروشی چندکشوری است که در سه کشور زیر فعالیت می‌کند:

- ایالات متحده آمریکا
- مکزیک
- کانادا

این شرکت دارای:

- **۲۴ فروشگاه**
- **۱۰٬۲۸۱ مشتری ثبت‌شده**
- **۱٬۵۶۰ محصول**
- **۱۱۱ برند**
- **۲۶۹٬۷۲۰ رکورد تراکنش فروش**
- **۷٬۰۸۷ رکورد مرجوعی**

پنج نوع فروشگاه موجود در داده عبارت‌اند از:

- Supermarket
- Deluxe Supermarket
- Gourmet Supermarket
- Mid-Size Grocery
- Small Grocery

### مدل کسب‌وکار

Maven Market محصولات غذایی و کالاهای مصرفی را از طریق فروشگاه‌های فیزیکی خود به مشتریان می‌فروشد. درآمد شرکت از فروش محصولات به دست می‌آید و سود ناخالص محصول بر اساس اختلاف بین قیمت فروش و هزینه محصول محاسبه می‌شود.

</div>

<div dir="ltr" align="left">

```text
Revenue = Quantity Sold × Retail Price
Product Cost = Quantity Sold × Product Cost
Gross Product Profit = Revenue − Product Cost
Gross Profit Margin = Gross Product Profit ÷ Revenue
```

</div>

<div dir="rtl" align="right">

مشتریان شرکت در چهار سطح عضویت دسته‌بندی شده‌اند:

- Normal
- Bronze
- Silver
- Golden

اطلاعات جمعیت‌شناختی و رفتاری قابل‌استفاده شامل درآمد سالانه، شغل، تحصیلات، وضعیت تأهل، تعداد فرزندان، مالکیت خانه، محل سکونت و تاریخ ایجاد حساب است.

---

## ۳. وضعیت فعلی شرکت

داده‌های Maven Market در هشت فایل CSV جداگانه نگهداری می‌شوند:

1. Calendar
2. Customers
3. Products
4. Regions
5. Stores
6. Returns
7. Transactions 1997
8. Transactions 1998

مدیران شرکت در حال حاضر نمای تحلیلی یکپارچه‌ای برای مشاهده عملکرد کل کسب‌وکار ندارند. اطلاعات فروش، هزینه، مشتری، محصول، فروشگاه، منطقه و مرجوعی در فایل‌های جداگانه قرار گرفته‌اند و برای پاسخ‌دادن به سؤالات مدیریتی باید به‌صورت صحیح به یکدیگر متصل شوند.

گزارش‌های پراکنده نمی‌توانند به‌سرعت نشان دهند که چه بخش‌هایی باعث رشد یا افت عملکرد شده‌اند، کدام فروشگاه‌ها و محصولات سودآورترند، یا کدام گروه‌های مشتری ارزش بیشتری ایجاد می‌کنند.

---

## ۴. مشکل اصلی کسب‌وکار

مدیران Maven Market نمی‌توانند به‌سرعت و با اطمینان پاسخ دهند:

- فروش و سود ناخالص شرکت در چه وضعیتی قرار دارد؟
- عملکرد سال ۱۹۹۸ نسبت به سال ۱۹۹۷ چگونه تغییر کرده است؟
- کدام کشورها، مناطق و فروشگاه‌ها بیشترین درآمد و سود را ایجاد می‌کنند؟
- کدام فروشگاه‌ها فروش بالا ولی حاشیه سود پایین دارند؟
- کدام محصولات و برندها بیشترین سهم فروش و سود را دارند؟
- کدام محصولات یا فروشگاه‌ها بیشترین میزان مرجوعی را ثبت کرده‌اند؟
- کدام گروه‌های مشتری ارزش بیشتری برای شرکت ایجاد می‌کنند؟
- عملکرد انواع فروشگاه چگونه با یکدیگر مقایسه می‌شود؟
- آیا اندازه فروشگاه با میزان فروش و سود آن متناسب است؟
- منابع شرکت باید روی کدام مناطق، فروشگاه‌ها، مشتریان یا محصولات متمرکز شوند؟

نبود یک مدل داده یکپارچه و داشبورد مدیریتی باعث می‌شود تصمیم‌ها با تأخیر یا بر اساس گزارش‌های ناقص گرفته شوند. همچنین ممکن است واحدهایی موفق تلقی شوند که فروش بالایی دارند، اما حاشیه سود یا نرخ مرجوعی آن‌ها نامطلوب است.

---

## ۵. بیان مسئله پروژه

</div>

<div dir="ltr" align="left">

### Business Problem Statement

Maven Market lacks a centralized analytical system for evaluating sales performance, gross product profitability, customer value, store productivity, product performance, and product returns across its retail network.

The company’s data is distributed across multiple transaction and reference files, making it difficult for executives and operational managers to identify performance trends, compare regions and stores, detect profitability risks, and prioritize growth opportunities.

The company needs an interactive business intelligence solution that transforms fragmented data into consistent KPIs, actionable insights, and decision-ready management views.

</div>

<div dir="rtl" align="right">

---

## ۶. نقش من در پروژه

در این سناریو، نقش من عبارت است از:

**Junior Data Analyst and Business Intelligence Developer**

مسئولیت من تبدیل داده‌های خام Maven Market به یک سیستم تحلیلی قابل‌اعتماد برای مدیران شرکت است.

### مسئولیت‌ها

- ارزیابی اولیه و کنترل کیفیت داده‌ها
- پاک‌سازی و استانداردسازی داده‌ها
- ترکیب فایل‌های تراکنش سال‌های ۱۹۹۷ و ۱۹۹۸
- طراحی مدل داده تحلیلی
- تعریف KPIهای مدیریتی
- انجام تحلیل اکتشافی داده‌ها
- ساخت داشبورد تعاملی Power BI
- استخراج Insightهای تجاری
- ارائه پیشنهادهای مدیریتی
- مستندسازی کامل پروژه در GitHub

---

## ۷. ذی‌نفعان اصلی

### مدیرعامل — Chief Executive Officer

نیازمند نمای کلی فروش، سودآوری، رشد، عملکرد مناطق و مهم‌ترین ریسک‌ها و فرصت‌هاست.

### مدیر مالی — Chief Financial Officer

نیازمند تحلیل درآمد، هزینه محصول، سود ناخالص، حاشیه سود و سهم بخش‌های مختلف در سودآوری است.

### مدیر فروش — Sales Director

باید عملکرد فروشگاه‌ها، مناطق، محصولات و مشتریان را مقایسه کند.

### مدیران منطقه‌ای — Regional Managers

باید عملکرد فروشگاه‌های تحت مدیریت خود را مشاهده و نقاط ضعف و فرصت‌های رشد را شناسایی کنند.

### مدیر عملیات فروشگاه‌ها — Store Operations Manager

به تحلیل بهره‌وری فروشگاه، اندازه فروشگاه، نوع فروشگاه و مرجوعی کالا نیاز دارد.

### مدیر محصول و دسته‌بندی — Product and Category Manager

باید محصولات و برندهای پرفروش، پرسود، کم‌سود و دارای مرجوعی بالا را شناسایی کند.

### مدیر مشتریان و وفاداری — Customer and Loyalty Manager

باید ارزش گروه‌های عضویت و ویژگی‌های مشتریان را تحلیل کند.

### تیم هوش تجاری — Business Intelligence Team

مسئول نگهداری مدل داده، KPIها، داشبورد و کنترل کیفیت گزارش‌هاست.

---

## ۸. استفاده‌کنندگان داشبورد

### کاربران سطح مدیریتی — Executive Users

- مدیرعامل
- مدیر مالی
- مدیر ارشد فروش

این کاربران به KPIهای کلان، روندها، هشدارها و فرصت‌ها نیاز دارند.

### کاربران سطح تاکتیکی — Tactical Users

- مدیران منطقه‌ای
- مدیر محصول
- مدیر مشتریان
- مدیر عملیات

این کاربران به مقایسه بخش‌ها و شناسایی عوامل عملکرد نیاز دارند.

### کاربران تحلیلی — Analytical Users

- تحلیلگران داده
- تیم Business Intelligence
- کارشناسان فروش و عملیات

این کاربران به فیلترها، Drill-through، جداول جزئیات و بررسی رکوردها نیاز دارند.

---

## ۹. تصمیم‌هایی که داشبورد پشتیبانی می‌کند

### تصمیم‌های فروش و رشد

- تمرکز بر مناطق یا فروشگاه‌های دارای ظرفیت رشد
- شناسایی فروشگاه‌های نیازمند مداخله
- مقایسه عملکرد سال‌ها، ماه‌ها و فصل‌ها
- شناسایی مناطق دارای رشد یا افت

### تصمیم‌های سودآوری

- شناسایی منابع اصلی سود
- تشخیص فروش بالا همراه با سودآوری پایین
- اولویت‌بندی محصولات و برندهای سودآور
- کاهش تمرکز روی محصولات کم‌بازده
- مقایسه حاشیه سود فروشگاه‌ها و مناطق

### تصمیم‌های محصول

- بهینه‌سازی ترکیب محصولات
- شناسایی محصولات پرفروش ولی کم‌سود
- شناسایی محصولات کم‌فروش ولی پرسود
- بررسی محصولات دارای مرجوعی بالا
- تعیین برندهای استراتژیک

### تصمیم‌های مشتری

- شناسایی مشتریان باارزش
- مقایسه سطوح عضویت
- بررسی ارزش مشتریان بر اساس ویژگی‌های جمعیت‌شناختی
- شناسایی گروه‌های مناسب برای برنامه‌های وفاداری
- بررسی تمرکز درآمد روی گروه محدودی از مشتریان

### تصمیم‌های فروشگاهی و عملیاتی

- مقایسه انواع فروشگاه
- بررسی بهره‌وری فروشگاه‌ها
- تحلیل فروش و سود نسبت به مساحت فروشگاه
- شناسایی فروشگاه‌های دارای مرجوعی بالا
- اولویت‌بندی فروشگاه‌ها برای توسعه یا بررسی عملیاتی

---

## ۱۰. اهداف اصلی تحلیل

### هدف ۱: ایجاد نمای یکپارچه عملکرد

ترکیب داده‌های فروش، مشتری، محصول، فروشگاه، منطقه و مرجوعی در یک مدل تحلیلی قابل‌اعتماد.

### هدف ۲: اندازه‌گیری عملکرد مالی

محاسبه و بررسی:

- Revenue
- Product Cost
- Gross Product Profit
- Gross Profit Margin
- Quantity Sold

### هدف ۳: تحلیل روند زمانی

بررسی روند فروش و سود در سطح روز، ماه، فصل و سال و مقایسه عملکرد ۱۹۹۸ با ۱۹۹۷.

### هدف ۴: تحلیل فروشگاه و منطقه

مقایسه فروشگاه‌ها، کشورها، مناطق فروش و انواع فروشگاه از نظر فروش، سود، حاشیه سود، تعداد مشتری، تعداد کالای فروخته‌شده، مرجوعی و بهره‌وری فضای فروشگاه.

### هدف ۵: تحلیل محصول و برند

شناسایی محصولات و برندهای پرفروش، پرسود، کم‌سود، دارای مرجوعی بالا و دارای فروش بالا ولی حاشیه سود پایین.

### هدف ۶: تحلیل مشتری

بررسی ارزش مشتریان بر اساس سطح عضویت، کشور، درآمد سالانه، شغل، تحصیلات، جنسیت، وضعیت تأهل، مالکیت خانه و تعداد فرزندان.

### هدف ۷: تحلیل مرجوعی

بررسی تعداد و نرخ مرجوعی به تفکیک زمان، محصول، برند، فروشگاه، نوع فروشگاه، کشور و منطقه.

### هدف ۸: تولید Insight قابل اقدام

تبدیل یافته‌های تحلیلی به پیشنهادهای روشن و اولویت‌بندی‌شده برای مدیران.

---

## ۱۱. KPIهای اولیه پروژه

> فهرست نهایی KPIها پس از Data Audit و بررسی Grain جداول تأیید خواهد شد.

### Executive KPIs

- Total Revenue
- Total Product Cost
- Gross Product Profit
- Gross Profit Margin
- Total Quantity Sold
- Active Customers
- Revenue Growth
- Profit Growth
- Return Quantity
- Return Rate

### Customer KPIs

- Revenue per Customer
- Profit per Customer
- Active Customers by Membership Tier
- Customer Revenue Contribution
- Repeat Customer Rate
- Top Customer Contribution

### Product KPIs

- Revenue by Product
- Profit by Product
- Product Profit Margin
- Product Sales Contribution
- Brand Revenue Contribution
- Product Return Rate

### Store KPIs

- Revenue per Store
- Profit per Store
- Revenue per Square Foot
- Profit per Square Foot
- Revenue per Grocery Square Foot
- Store Return Rate
- Store Type Contribution

---

## ۱۲. محدوده پروژه

### موارد داخل محدوده

- تراکنش‌های فروش سال‌های ۱۹۹۷ و ۱۹۹۸
- اطلاعات مشتریان
- اطلاعات محصولات و برندها
- اطلاعات فروشگاه‌ها و مناطق
- مرجوعی محصولات
- قیمت فروش و هزینه محصول
- ویژگی‌های فروشگاه
- ویژگی‌های جمعیت‌شناختی مشتریان
- تحلیل زمانی
- تحلیل فروش و سود ناخالص محصول
- تحلیل محصول و برند
- تحلیل مشتری
- تحلیل فروشگاه و منطقه
- تحلیل مرجوعی
- مدل‌سازی داده
- ساخت داشبورد Power BI
- گزارش مدیریتی و پیشنهادهای تجاری

---

## ۱۳. موارد خارج از محدوده

### تحلیل تخفیف

دیتاست ستون تخفیف ندارد؛ بنابراین اثر تخفیف بر فروش یا سود قابل‌اندازه‌گیری نیست.

### تحلیل کانال فروش

داده‌ای درباره فروش آنلاین، حضوری یا کانال‌های مختلف فروش وجود ندارد.

### تحلیل وضعیت سفارش

دیتاست دارای Order Status نیست.

### Average Order Value واقعی

شناسه سفارش یا Basket ID وجود ندارد. هر ردیف یک رکورد فروش محصول است و نباید بدون بررسی به‌عنوان یک سفارش کامل در نظر گرفته شود.

### سود خالص حسابداری

هزینه موجود در داده فقط هزینه محصول است. هزینه‌های حقوق، اجاره، مالیات، انرژی، بازاریابی، لجستیک و اداری در دسترس نیستند. بنابراین معیار سود با عنوان **Gross Product Profit** معرفی می‌شود، نه Net Profit.

### اتصال مرجوعی به مشتری

جدول Returns دارای `customer_id` نیست؛ بنابراین امکان تعیین مشتری مرجوع‌کننده وجود ندارد.

### اتصال مستقیم مرجوعی به تراکنش

جدول Returns فاقد Order ID یا Transaction ID است؛ بنابراین مرجوعی‌ها فقط در سطح محصول، فروشگاه و زمان تحلیل می‌شوند.

### Machine Learning پیشرفته

نسخه اصلی پروژه شامل الگوریتم‌های پیچیده Machine Learning نیست و این موارد فقط به‌عنوان توسعه آینده مطرح خواهند شد.

---

## ۱۴. محدودیت‌های پروژه

- داده‌ها مربوط به سال‌های ۱۹۹۷ و ۱۹۹۸ هستند.
- شرکت و سناریوی Maven Market آموزشی و فرضی است.
- شناسه سفارش وجود ندارد.
- تخفیف و کمپین بازاریابی ثبت نشده است.
- هزینه‌های کامل عملیاتی وجود ندارند.
- امکان محاسبه سود خالص وجود ندارد.
- اطلاعات موجودی کالا در دسترس نیست.
- مرجوعی‌ها به مشتری یا تراکنش اصلی متصل نیستند.
- علت مرجوعی ثبت نشده است.
- اهداف فروش یا بودجه برنامه‌ریزی‌شده وجود ندارند.
- تحلیل علیت با این داده امکان‌پذیر نیست.
- نتایج پروژه باید به‌عنوان تحلیل داده تاریخی معرفی شوند.

---

## ۱۵. خروجی‌های نهایی پروژه

### خروجی‌های داده‌ای

- نسخه آرشیوی داده خام
- داده پاک‌سازی‌شده
- جداول آماده تحلیل
- Data Dictionary
- Data Quality Report
- Cleaning Log

### خروجی‌های فنی

- Python Cleaning Script
- Jupyter Notebooks
- SQL Scripts
- Dimensional Data Model
- Power Query Transformations
- DAX Measures
- Power BI Dashboard

### خروجی‌های تحلیلی

- Exploratory Data Analysis
- KPI Dictionary
- Business Insights
- Executive Summary
- Business Recommendations
- Management Report

### خروجی‌های پورتفولیو

- GitHub Repository
- Professional README
- Dashboard Screenshots
- Dashboard PDF
- Resume Bullet Points
- LinkedIn Project Description
- LinkedIn Launch Post
- Interview Presentation
- Interview Questions and Answers

---

## ۱۶. ساختار پیشنهادی داشبورد

1. **Executive Overview** — نمای کلی فروش، سود، رشد، مشتری، منطقه و هشدارها
2. **Sales & Trend Performance** — تحلیل روند زمانی و مقایسه دوره‌ها و فروشگاه‌ها
3. **Product & Brand Profitability** — تحلیل محصولات، برندها، فروش و سودآوری
4. **Customer Value Analysis** — تحلیل مشتریان، عضویت و ویژگی‌های جمعیت‌شناختی
5. **Store & Geographic Performance** — تحلیل کشور، منطقه، فروشگاه و بهره‌وری فضا
6. **Returns & Detailed Analysis** — تحلیل مرجوعی و دسترسی به جزئیات

---

## ۱۷. Project Brief

</div>

<div dir="ltr" align="left">

### Business Context

Maven Market Group is a multi-country grocery and consumer retail company operating 24 stores across the United States, Mexico, and Canada.

The company serves 10,281 registered customers and offers 1,560 products from 111 brands through five different store formats. The available data covers 269,720 sales transaction records and 7,087 return records during 1997 and 1998, along with detailed information about customers, products, stores, and sales regions.

### Business Problem

Maven Market’s data is distributed across multiple CSV files, and management does not have a centralized analytical view of business performance.

Executives and managers are unable to quickly compare revenue, gross product profit, customer value, store performance, product performance, and product returns across time periods and business units. This limits their ability to identify growth opportunities, detect profitability risks, and prioritize corrective actions.

### Project Objective

The objective of this project is to build an end-to-end retail business intelligence solution that transforms Maven Market’s raw data into a reliable analytical model, decision-oriented KPIs, interactive Power BI dashboards, and actionable business recommendations.

### Stakeholders

- Chief Executive Officer
- Chief Financial Officer
- Sales Director
- Regional Managers
- Store Operations Manager
- Product and Category Manager
- Customer and Loyalty Manager
- Business Intelligence Team

### Analytical Approach

1. Data auditing and quality assessment
2. Data cleaning and standardization with Python
3. Data transformation and integration
4. Dimensional data modeling
5. Exploratory data analysis
6. KPI definition and validation
7. Power BI dashboard development
8. Management insight generation
9. Business recommendation development
10. GitHub and portfolio documentation

### Tools and Technologies

- Python
- Pandas
- NumPy
- Matplotlib
- Jupyter Notebook
- SQL Server
- Power Query
- Power BI
- DAX
- Git
- GitHub

### Expected Business Value

The final solution is expected to provide Maven Market with:

- A consistent and centralized view of retail performance
- Faster identification of sales and profitability trends
- Improved comparison of stores, regions, products, and customer groups
- Better visibility into product return patterns
- Improved prioritization of growth opportunities
- More informed product and store decisions
- A reliable KPI framework for management reporting
- Faster and more evidence-based decision-making

</div>

<div dir="rtl" align="right">

---

## ۱۸. خلاصه حرفه‌ای پروژه

Maven Market Group به یک راهکار یکپارچه هوش تجاری نیاز دارد تا عملکرد فروش، سود ناخالص محصول، ارزش مشتری، بهره‌وری فروشگاه، عملکرد محصولات و الگوهای مرجوعی را در ۲۴ فروشگاه و سه کشور ارزیابی کند.

در نقش Data Analyst و BI Developer، داده‌های خام شرکت را ارزیابی و پاک‌سازی می‌کنم، یک مدل داده تحلیلی طراحی می‌کنم، KPIهای مدیریتی را تعریف می‌کنم و یک داشبورد تعاملی Power BI می‌سازم.

راهکار نهایی به مدیران کمک خواهد کرد شکاف‌های عملکرد، ریسک‌های سودآوری، گروه‌های مشتری ارزشمند، محصولات با عملکرد قوی و فرصت‌های رشد را شناسایی کنند.

---

## ۱۹. معیار تکمیل مرحله اول

- [x] مسئله کسب‌وکار مشخص شده است.
- [x] نقش تحلیلگر تعریف شده است.
- [x] ذی‌نفعان و کاربران داشبورد مشخص شده‌اند.
- [x] تصمیم‌های مورد پشتیبانی تعریف شده‌اند.
- [x] اهداف تحلیل با داده‌های واقعی سازگارند.
- [x] محدوده و محدودیت‌های پروژه شفاف شده‌اند.
- [x] از ادعاهای فاقد داده جلوگیری شده است.
- [x] خروجی‌های نهایی پروژه تعریف شده‌اند.
- [x] Project Brief انگلیسی آماده شده است.
- [x] عنوان پروژه برای رزومه و GitHub مناسب است.

</div>
