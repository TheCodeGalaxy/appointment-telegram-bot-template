# Appointment Booking Telegram Bot

A production-ready, bilingual Telegram bot for managing appointments — built with `python-telegram-bot` (v21) and async SQLAlchemy 2.0.

Customers book through a guided conversation, admins get a clean daily overview, cancellation controls, bulk service import, and automatic background cleanup. No manual maintenance required.

---

## 🚀 Why This Template?

Skip weeks of boilerplate work. This bot gives you:

- ✅ Guided booking flow (service → individuals → date → time → confirm)
- ✅ Fast-Track checkout (returning users skip name/phone)
- ✅ Admin panel with daily indexing (1, 2, 3… resets daily)
- ✅ Bulk service import via Excel/CSV
- ✅ Anti-double-booking (database-level unique constraint)
- ✅ Bilingual (EN/AR) with Arabic dates
- ✅ Automatic cleanup (7 days for admin, 14 days for users)
- ✅ Tested, documented, ready to run

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Bot | python-telegram-bot 21.3 |
| Database | SQLite + aiosqlite |
| ORM | SQLAlchemy 2.0 async |
| Config | pydantic-settings |
| Spreadsheets | pandas + openpyxl |
| Language | Python 3.12+ |

---


## 🆕 Getting Your Bot Token & Admin ID

Before setting up the bot, you need to create a Telegram bot and get your admin ID.

### 1. Create a Bot and Get Token
- Open Telegram and search for **@BotFather**
- Send `/newbot` and follow the instructions
- Choose a name for your bot (e.g., `My Booking Bot`)
- Choose a username ending with `bot` (e.g., `mybooking_bot`)
- After creation, you will receive a **Bot Token** (e.g., `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
- **Save this token** — you will need it in `.env` file

### 2. Get Your Telegram Admin ID
- Search for **@userinfobot** in Telegram
- Send `/start`
- The bot will reply with your **Telegram ID** (a number like `123456789`)
- **Save this ID** — you will need it in `.env` file

---

## 📥 Prerequisites (Install Python 3.12)

If you don't have Python 3.12+ installed, run the appropriate command for your OS:

- **Windows (CMD/PowerShell):** `winget install -e --id Python.Python.3.12` (Restart your Terminal after install)
- **Linux (Ubuntu):** `sudo apt update && sudo apt install python3.12 python3.12-venv python3-pip -y`
- **Mac:** `brew install python@3.12`

## ⚙️ Linux & Mac Setup

```bash 
# download vs code IDE and open project folder then write this commands in the terminal
cd appointment-bot-template
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set BOT_TOKEN and ADMIN_IDS in .env file
python -m bot.main
# Now submit your data exel or csv file as example.xlsx or example.csv to the bot then /start
```

### Windows Setup (PowerShell)

```powershell
# download vs code IDE and open project folder then write this commands in the terminal
cd appointment-bot-template
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Set BOT_TOKEN and ADMIN_IDS in .env file
python -m bot.main
# Now submit your data exel or csv file as example.xlsx or example.csv to the bot then /start
```

### Windows Setup (CMD)
```cmd
cd appointment-bot-template
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
python -m bot.main
```

The bot initializes the database and registers the daily retention job automatically.

---

## 📁 What You Get

```
appointment-bot-template/
├── bot/                # Complete source code
│   ├── handlers/       # /start, booking FSM, admin panel
│   ├── services/       # Booking logic, scheduling, import, retention
│   ├── database/       # SQLAlchemy models + connection
│   ├── utils/          # Keyboards, validators, FSM states
│   └── locales/        # EN/AR messages
├── tests/              # pytest suite
├── data/               # SQLite database (auto-created)
├── requirements.txt
├── .env.example
└── README.md
```

---

## 📋 Key Features

| Feature | Description |
|---------|-------------|
| **Guided booking** | Inline buttons, live available slots, past dates blocked |
| **Fast-Track** | Returning users skip name/phone entry |
| **Admin panel** | `/admin` → today/upcoming bookings with daily indexing (1,2,3…) |
| **Bulk import** | Upload `.xlsx` / `.csv` (title, duration_minutes, is_active) |
| **Retention policy** | Admin: 7 days, User: 14 days — automatic daily purge |
| **Anti-double-booking** | Database `UNIQUE` constraint on (date, start_time) |
| **Bilingual** | Full EN/AR with Arabic weekdays/months |
| **Testing** | `pytest` suite ready |

---

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BOT_TOKEN` | — | Telegram bot token (required) |
| `ADMIN_IDS` | — | Comma-separated admin Telegram IDs |
| `DATABASE_PATH` | `data/appointments.db` | SQLite file path |
| `SLOT_DURATION_MINUTES` | `30` | Default slot length |
| `WORKING_HOURS_START/END` | `09:00` / `18:00` | Business hours |
| `WORKING_DAYS` | `0,1,2,3,4` | 0=Monday, 6=Sunday |
| `DEFAULT_LANGUAGE` | `en` | `en` or `ar` |
| `MIN/MAX_BOOKING_INDIVIDUALS` | `1` / `10` | Per-booking range |
| `ADMIN_RETENTION_DAYS` | `7` | Admin history retention |
| `USER_RETENTION_DAYS` | `14` | User history retention |

---

## 🧪 Testing

```bash
pytest
```

All tests run in-memory, no external dependencies.

---

## 📄 License

Provided as a template. Adjust as needed.

---

---

# 🤖 بوت حجز المواعيد لتليجرام

بوت جاهز للإنتاج، ثنائي اللغة، لإدارة حجز المواعيد — مبني بـ `python-telegram-bot` (v21) و SQLAlchemy 2.0 غير المتزامن.

يحجز العملاء عبر محادثة موجّهة، ويوفر للمشرفين لوحة تحكم يومية نظيفة، وأدوات إلغاء، واستيراد جماعي للخدمات، وتنظيف تلقائي في الخلفية. لا حاجة لأي صيانة يدوية.

---

## 🚀 لماذا هذا القالب؟

تخطّ أسابيع من العمل التمهيدي. هذا البوت يمنحك:

- ✅ تدفق حجز موجّه (خدمة → عدد الأفراد → تاريخ → وقت → تأكيد)
- ✅ دفع سريع (المستخدمون العائدون يتخطون إدخال الاسم/الهاتف)
- ✅ لوحة تحكم للمشرف بترقيم يومي (1، 2، 3… يُعاد ضبطه يومياً)
- ✅ استيراد جماعي للخدمات عبر Excel/CSV
- ✅ منع الحجز المزدوج (عبر قيد فريد في قاعدة البيانات)
- ✅ دعم لغتين (عربي/إنجليزي) مع تواريخ عربية
- ✅ تنظيف تلقائي (7 أيام للمشرف، 14 يوماً للمستخدم)
- ✅ مُختبر، موثق، وجاهز للتشغيل

---

## 🛠️ الأدوات التقنية

| الطبقة | التقنية |
|--------|---------|
| البوت | python-telegram-bot 21.3 |
| قاعدة البيانات | SQLite + aiosqlite |
| ORM | SQLAlchemy 2.0 غير متزامن |
| الإعدادات | pydantic-settings |
| جداول البيانات | pandas + openpyxl |
| اللغة | Python 3.12+ |

---

## 🆕 الحصول على توكن البوت ومعرف المشرف

قبل البدء في إعداد البوت، تحتاج إلى إنشاء بوت تليجرام والحصول على معرف المشرف الخاص بك.

### 1. إنشاء بوت والحصول على التوكن
- افتح تليجرام وابحث عن **@BotFather**
- أرسل `/newbot` واتبع التعليمات
- اختر اسماً للبوت (مثل `My Booking Bot`)
- اختر اسم مستخدم ينتهي بـ `bot` (مثل `mybooking_bot`)
- بعد الإنشاء، ستحصل على **توكن البوت** (مثل `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
- **احفظ هذا التوكن** — ستحتاجه في ملف `.env`

### 2. الحصول على معرف المشرف في تليجرام
- ابحث عن **@userinfobot** في تليجرام
- أرسل `/start`
- سيرد البوت برقم **معرفك** (رقم مثل `123456789`)
- **احفظ هذا الرقم** — ستحتاجه في ملف `.env`

---

## 📥 المتطلبات الأساسية (تثبيت Python 3.12)

إذا لم يكن لديك Python 3.12+ مثبتاً، شغّل الأمر المناسب لنظامك:

- **ويندوز (CMD/PowerShell):** `winget install -e --id Python.Python.3.12` (أعد تشغيل الطرفية بعد التثبيت)
- **لينكس (أوبونتو):** `sudo apt update && sudo apt install python3.12 python3.12-venv python3-pip -y`
- **ماك:** `brew install python@3.12`

## ⚙️ إعداد لينكس وماك

```bash
# حمل برنامج VS Code وافتح مجلد المشروع ثم اكتب هذه الأوامر في الطرفية
cd appointment-bot-template
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# ضع BOT_TOKEN و ADMIN_IDS في ملف .env
python -m bot.main
# الان ارسل ملف بياناتك Excel أو CSV مثل ملف (مثال.xlsx) أو (مثال.csv) للبوت ثم استخدم أمر /start
```

### إعداد ويندوز (PowerShell)

```powershell
# حمل برنامج VS Code وافتح مجلد المشروع ثم اكتب هذه الأوامر في الطرفية
cd appointment-bot-template
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# ضع BOT_TOKEN و ADMIN_IDS في ملف .env
python -m bot.main
# الان ارسل ملف بياناتك Excel أو CSV مثل ملف (مثال.xlsx) أو (مثال.csv) للبوت ثم استخدم أمر /start
```

### إعداد ويندوز (CMD)

```cmd
cd appointment-bot-template
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
python -m bot.main
```


البوت يُنشئ قاعدة البيانات ويسجّل مهمة التنظيف اليومية تلقائياً.
```


---

## 📁 ماذا تحصل؟

```
appointment-bot-template/
├── bot/                # الكود المصدري الكامل
│   ├── handlers/       # /start، الحجز، لوحة المشرف
│   ├── services/       # منطق الحجز، الجدولة، الاستيراد، التنظيف
│   ├── database/       # نماذج SQLAlchemy + الاتصال
│   ├── utils/          # لوحات المفاتيح، المدققات، حالات FSM
│   └── locales/        # رسائل عربي/إنجليزي
├── tests/              # اختبارات pytest
├── data/               # قاعدة بيانات SQLite (تُنشأ تلقائياً)
├── requirements.txt
├── .env.example
└── README.md
```

---

## 📋 الميزات الرئيسية

| الميزة | الوصف |
|--------|-------|
| **حجز موجّه** | أزرار تفاعلية، مواعيد متاحة مباشرة، تواريخ ماضية ممنوعة |
| **دفع سريع** | المستخدمون العائدون يتخطون إدخال الاسم/الهاتف |
| **لوحة المشرف** | `/admin` → حجوزات اليوم والقادمة بترقيم يومي (1،2،3…) |
| **استيراد جماعي** | رفع ملف `.xlsx` / `.csv` (العنوان، المدة، is_active) |
| **سياسة الاحتفاظ** | المشرف: 7 أيام، المستخدم: 14 يوماً — تنظيف تلقائي يومي |
| **منع الحجز المزدوج** | قيد `UNIQUE` في قاعدة البيانات على (التاريخ، وقت البدء) |
| **دعم لغتين** | عربي/إنجليزي بالكامل مع أيام وأشهر عربية |
| **الاختبارات** | مجموعة `pytest` جاهزة |

---

## 🔧 متغيرات البيئة

| المتغير | القيمة الافتراضية | الوصف |
|---------|-------------------|-------|
| `BOT_TOKEN` | — | رمز البوت من @BotFather (مطلوب) |
| `ADMIN_IDS` | — | معرفات المشرفين مفصولة بفواصل |
| `DATABASE_PATH` | `data/appointments.db` | مسار ملف SQLite |
| `SLOT_DURATION_MINUTES` | `30` | المدة الافتراضية للحجز |
| `WORKING_HOURS_START/END` | `09:00` / `18:00` | ساعات العمل |
| `WORKING_DAYS` | `0,1,2,3,4` | 0=الإثنين، 6=الأحد |
| `DEFAULT_LANGUAGE` | `en` | `en` أو `ar` |
| `MIN/MAX_BOOKING_INDIVIDUALS` | `1` / `10` | نطاق عدد الأفراد |
| `ADMIN_RETENTION_DAYS` | `7` | احتفاظ المشرف |
| `USER_RETENTION_DAYS` | `14` | احتفاظ المستخدم |

---

## 🧪 الاختبارات

```bash
pytest
```

جميع الاختبارات تعمل في الذاكرة، ولا تحتاج اتصالاً خارجياً.

---

## 📄 الترخيص

يُقدم كقالب. عدّل الترخيص حسب حاجتك.