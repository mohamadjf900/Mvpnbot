FROM python:3.10-slim

WORKDIR /app

# کپی کردن لیست نیازمندی‌ها
COPY requirements.txt .

# نصب کتابخانه‌ها بدون کش برای سبک ماندن داکر
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن کل فایل‌های پروژه به داخل کانتینر
COPY . .

# باز کردن پورت 10000 برای سرور وب رندر
EXPOSE 10000

# دستور نهایی برای اجرای سرور وب و ربات
CMD ["python", "app.py"]
