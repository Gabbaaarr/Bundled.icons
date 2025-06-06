# Use Python 3.11 slim image as base
FROM python:3.11-slim

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

# Create directory for static files
RUN mkdir -p /app/static

# Temporarily set STATICFILES_STORAGE to local storage for build
ENV STATICFILES_STORAGE=django.contrib.staticfiles.storage.StaticFilesStorage

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

# Create startup script
RUN echo '#!/bin/bash\n\
# Activate virtual environment\n\
source /opt/venv/bin/activate\n\
# Set S3 storage for runtime\n\
export STATICFILES_STORAGE=storages.backends.s3boto3.S3Boto3Storage\n\
# Start Django\n\
python manage.py runserver 0.0.0.0:8000\n\
' > /app/start.sh && chmod +x /app/start.sh

# Start Django
CMD ["/app/start.sh"] 