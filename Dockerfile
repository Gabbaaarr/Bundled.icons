# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create directory for static files
RUN mkdir -p /app/static

# Temporarily set STATICFILES_STORAGE to local storage for build
ENV STATICFILES_STORAGE=django.contrib.staticfiles.storage.StaticFilesStorage

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port 80
EXPOSE 80

# Create startup script
RUN echo '#!/bin/bash\n\
# Activate virtual environment\n\
source /opt/venv/bin/activate\n\
# Set S3 storage for runtime\n\
export STATICFILES_STORAGE=storages.backends.s3boto3.S3Boto3Storage\n\
service nginx start\n\
python manage.py runserver 0.0.0.0:8000\n\
' > /app/start.sh && chmod +x /app/start.sh

# Start Nginx and Django
CMD ["/app/start.sh"] 