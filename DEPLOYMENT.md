# Deployment Guide for AWS EC2

## Prerequisites
1. An AWS EC2 instance running Ubuntu (recommended: Ubuntu 22.04 LTS)
2. An Elastic IP associated with your EC2 instance
3. AWS credentials configured on your local machine
4. Domain name (optional, but recommended)

## Step 1: Update System and Install Dependencies
```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv nginx supervisor
```

## Step 2: Set Up Python Environment
```bash
# Create a directory for the application
sudo mkdir -p /var/www/bundled-icons
sudo chown ubuntu:ubuntu /var/www/bundled-icons

# Create and activate virtual environment
cd /var/www/bundled-icons
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
pip install gunicorn
```

## Step 3: Configure Environment Variables
```bash
# Create .env file
sudo nano /var/www/bundled-icons/.env

# Add the following content (replace with your actual values):
DJANGO_SECRET_KEY=your-secret-key
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=ap-south-1
AWS_CLOUDFRONT_DOMAIN=your-cloudfront-domain
AWS_CLOUDFRONT_DISTRIBUTION_ID=your-cloudfront-distribution-id
```

## Step 4: Configure Nginx
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/bundled-icons

# Add the following configuration:
server {
    listen 80;
    server_name your-elastic-ip;  # Replace with your Elastic IP or domain

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/bundled-icons;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_redirect off;
    }
}

# Enable the site
sudo ln -s /etc/nginx/sites-available/bundled-icons /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## Step 5: Configure Gunicorn
```bash
# Create Gunicorn service file
sudo nano /etc/supervisor/conf.d/bundled-icons.conf

# Add the following configuration:
[program:bundled-icons]
directory=/var/www/bundled-icons
command=/var/www/bundled-icons/venv/bin/gunicorn iconhub.wsgi:application --workers 3 --bind unix:/run/gunicorn.sock
autostart=true
autorestart=true
stderr_logfile=/var/log/bundled-icons/gunicorn.err.log
stdout_logfile=/var/log/bundled-icons/gunicorn.out.log
user=ubuntu
group=www-data

# Create log directory
sudo mkdir -p /var/log/bundled-icons
sudo chown ubuntu:ubuntu /var/log/bundled-icons

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
```

## Step 6: Deploy Application
```bash
# Clone your repository (if not already done)
cd /var/www/bundled-icons
git clone your-repository-url .

# Collect static files
python manage.py collectstatic --noinput

# Apply migrations
python manage.py migrate

# Restart Gunicorn
sudo supervisorctl restart bundled-icons
```

## Step 7: Set Up SSL (Optional but Recommended)
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Certbot will automatically modify your Nginx configuration
```

## Step 8: Final Checks
1. Ensure your EC2 security group allows:
   - HTTP (port 80)
   - HTTPS (port 443)
   - SSH (port 22)
2. Verify your Elastic IP is correctly associated with your EC2 instance
3. Test the application by visiting your Elastic IP or domain in a browser

## Monitoring and Maintenance
```bash
# Check application logs
sudo tail -f /var/log/bundled-icons/gunicorn.err.log
sudo tail -f /var/log/bundled-icons/gunicorn.out.log

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Restart services if needed
sudo systemctl restart nginx
sudo supervisorctl restart bundled-icons
```

## Backup and Recovery
1. Regularly backup your database
2. Keep a copy of your .env file
3. Document any custom configurations

## Troubleshooting
1. If the application doesn't start:
   - Check logs: `sudo tail -f /var/log/bundled-icons/gunicorn.err.log`
   - Verify environment variables: `cat /var/www/bundled-icons/.env`
   - Check permissions: `ls -la /var/www/bundled-icons`

2. If Nginx shows 502 Bad Gateway:
   - Check if Gunicorn is running: `sudo supervisorctl status`
   - Verify socket file: `ls -l /run/gunicorn.sock`
   - Check Nginx error logs: `sudo tail -f /var/log/nginx/error.log`

3. If static files aren't loading:
   - Verify static files collection: `python manage.py collectstatic --noinput`
   - Check Nginx configuration for static files location
   - Verify file permissions in static directory 