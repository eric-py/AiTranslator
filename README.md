# 📚 مترجم هوشمند کتاب با هوش مصنوعی Gemini | AI-Powered Book Translator with Gemini

**پروژه‌ای برای استخراج و ترجمه خودکار کتاب‌های PDF با استفاده از هوش مصنوعی Gemini و Django.**  
**A project for automatic extraction and translation of PDF books using Gemini AI and Django.**

---

## ✨ ویژگی‌ها | Features

- **استخراج متن از PDF با دقت بالا | High-Accuracy Text Extraction from PDFs**
- **ترجمه خودکار با Gemini AI | AI-Powered Automatic Translation**
- **ترجمه تک صفحه یا کل کتاب | Translate Single Pages or Entire Books**
- **مدیریت صف کاربران با Celery و Redis | Queue Management with Celery & Redis**
- **رابط کاربری واکنش‌گرا با Tailwind CSS | Responsive UI with Tailwind CSS**
- **اطلاع‌رسانی با ایمیل | Email Notifications**

---

## 🛠 پیش‌نیازها | Prerequisites

برای اجرای این پروژه به موارد زیر نیاز دارید:  
You need the following to run this project:

- **Python 3.10+**
- **Node.js & npm**
- **Docker**
- **wkhtmltopdf**
- **Google Gemini API Key**

---

## 🚀 نصب و راه‌اندازی | Installation & Setup

### 1️⃣ نصب `wkhtmltopdf` | Install `wkhtmltopdf`

```bash
sudo apt install wkhtmltopdf
```

### 2️⃣ کلون کردن مخزن | Clone the Repository

```bash
git clone https://github.com/eric-py/AiTranslator.git
cd AiTranslator
```

### 3️⃣ ساخت و فعال‌سازی محیط مجازی | Create and Activate a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate  # Windows
```

### 4️⃣ نصب وابستگی‌های Python | Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5️⃣ راه‌اندازی Redis با Docker | Start Redis with Docker

```bash
docker run -p 6379:6379 --name redis redis:8.0-M02-alpine
```

### 6️⃣ نصب و کامپایل Tailwind | Install and Compile Tailwind

```bash
python manage.py tailwind install
python manage.py tailwind start
```

### 7️⃣ تنظیم متغیرهای محیطی | Configure Environment Variables

```bash
cp backend/.env_file backend/.env
```

سپس فایل `.env` را ویرایش کرده و مقادیر زیر را تنظیم کنید:  
Then edit the `.env` file and set the following values:

- `SECRET_KEY_ENV`
- `DEBUG_MODE_ENV`
- `EMAIL_HOST_ENV`
- `EMAIL_HOST_USER_ENV`
- `EMAIL_HOST_PASSWORD_ENV`
- `GEMINI_API_KEY`

### 8️⃣ اجرای مایگریشن‌ها | Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 9️⃣ ایجاد کاربر ادمین | Create an Admin User

```bash
python manage.py createsuperuser
```

### 🔟 اجرای سرور توسعه | Run Development Server

```bash
python manage.py runserver
```

### 1️⃣1️⃣ اجرای Celery Worker | Run Celery Worker

```bash
celery -A core worker -l info -Q default,users
```

### 1️⃣2️⃣ اجرای Celery Beat | Run Celery Beat

```bash
celery -A core beat -l info
```

---

## 📂 ساختار پروژه | Project Structure

```
book-translator/
├── backend/
│   ├── account/        # اپلیکیشن مدیریت کاربران | User Management App
│   ├── books/          # اپلیکیشن مدیریت کتاب‌ها | Books Management App
│   ├── core/           # تنظیمات اصلی پروژه | Core Project Settings
│   ├── dashboard/      # اپلیکیشن داشبورد | Dashboard App
│   ├── extensions/     # ابزارهای جانبی | Utility Extensions
│   ├── theme/          # تنظیمات Tailwind | Tailwind Configuration
│   └── translator/     # اپلیکیشن ترجمه | Translation App
├── frontend/
│   ├── media/          # فایل‌های آپلود شده | Uploaded Files
│   ├── static/         # فایل‌های استاتیک | Static Files
│   └── templates/      # قالب‌های HTML | HTML Templates
└── requirements.txt    # وابستگی‌های Python | Python Dependencies
```

---

## ⚠️ نکات مهم | Important Notes

1. اطمینان حاصل کنید که Redis در حال اجراست:  
    Ensure Redis is running:
    
    ```bash
    docker ps | grep redis
    ```
    
2. برای اجرای مجدد Redis بعد از راه‌اندازی سیستم:  
    Restart Redis after system reboot:
    
    ```bash
    docker start redis
    ```
    
3. مسیرهای ضروری به صورت خودکار ساخته می‌شوند:  
    Required directories are automatically created:
    
    - `frontend/media/books/files/`
    - `frontend/media/books/covers/`

---