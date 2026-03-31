# ========================================
# Dockerfile احترافي لتطبيق FastAPI
# ========================================

# 1️⃣ استخدم صورة Python خفيفة
FROM python:3.10-slim

# 2️⃣ ضبط متغير البيئة لمنع Python من إنشاء ملفات .pyc
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=120

# 3️⃣ إنشاء مجلد العمل
WORKDIR /app

# 4️⃣ تثبيت المتطلبات الأساسية لنظام التشغيل (مثل gcc عند الحاجة)
# لتجنب مشاكل تثبيت بعض الحزم التي تحتاج بناء native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# 5️⃣ نسخ requirements.txt أولًا لاستخدام Docker cache
COPY requirements.txt .

# 6️⃣ تثبيت الاعتمادات باستخدام mirror سريع مع retries
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt -i https://pypi.org/simple --retries 5

# 7️⃣ نسخ باقي ملفات المشروع
COPY . .

# 8️⃣ أمر التشغيل الافتراضي
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]