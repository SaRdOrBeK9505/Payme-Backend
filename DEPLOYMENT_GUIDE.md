# 🚀 Production Deployment Guide

## Production Settings

### .env fayli (Production)
```env
# Django Settings
SECRET_KEY=<50+ characters random string>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Payme Configuration (Production)
PAYME_MERCHANT_ID=your_production_merchant_id
PAYME_KEY=your_production_payme_key
PAYME_ACCOUNT_FIELD=order_id
PAYME_ALLOWED_IPS=185.178.51.131,185.178.51.132,195.158.31.134,195.158.31.10
```

### settings.py ga qo'shish kerak (Production)

```python
# Security settings (production)
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
```

## Deployment Checklist

### 1. Environment Configuration
- [ ] `.env` fayl to'g'ri sozlangan
- [ ] `DEBUG=False` set qilingan
- [ ] `SECRET_KEY` 50+ characters
- [ ] `ALLOWED_HOSTS` to'g'ri domenlar
- [ ] Firebase credentials file mavjud

### 2. Database
- [ ] Firestore production database configured
- [ ] Firestore indexes created
- [ ] Database backup policy configured

### 3. Security
- [ ] SSL certificate o'rnatilgan
- [ ] HTTPS redirect enabled
- [ ] Security headers configured
- [ ] IP whitelist configured (Payme)

### 4. Static Files
```bash
python manage.py collectstatic --noinput
```

### 5. Migrations
```bash
python manage.py migrate
```

### 6. Logs Directory
```bash
mkdir logs
```

### 7. Test Production
```bash
python manage.py check --deploy
```

## Server Requirements

### Minimum Requirements
- Python 3.8+
- 1 GB RAM
- 10 GB disk space
- Ubuntu 20.04+ / CentOS 7+ / Windows Server 2019+

### Recommended Stack
- **Web Server:** Nginx
- **WSGI Server:** Gunicorn / uWSGI
- **Process Manager:** Supervisor / systemd
- **Database:** Google Firestore
- **Cache:** Redis (optional)
- **Queue:** Celery + Redis (optional)

## Deployment Options

### Option 1: Traditional VPS (Ubuntu)

#### 1. Install dependencies
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx supervisor
```

#### 2. Setup virtual environment
```bash
cd /var/www/payme_backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

#### 3. Gunicorn configuration
```bash
# /etc/supervisor/conf.d/payme_backend.conf
[program:payme_backend]
command=/var/www/payme_backend/venv/bin/gunicorn core.wsgi:application --bind 127.0.0.1:8000 --workers 3
directory=/var/www/payme_backend
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/payme_backend/gunicorn.log
stderr_logfile=/var/log/payme_backend/gunicorn.err.log
```

#### 4. Nginx configuration
```nginx
# /etc/nginx/sites-available/payme_backend
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /var/www/payme_backend/static/;
    }
}
```

#### 5. Enable and start services
```bash
sudo ln -s /etc/nginx/sites-available/payme_backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start payme_backend
```

### Option 2: Docker

#### Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./secrets:/app/secrets
    restart: always
```

#### Deploy
```bash
docker-compose up -d
```

### Option 3: Cloud Platforms

#### Railway
```bash
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn core.wsgi:application"
```

#### Heroku
```bash
# Procfile
web: gunicorn core.wsgi:application
```

#### Google Cloud Run
```bash
gcloud run deploy payme-backend --source .
```

## Monitoring

### Health Check Endpoint
```python
# payments/views.py
from rest_framework.views import APIView
from rest_framework.response import Response

class HealthCheckView(APIView):
    def get(self, request):
        return Response({"status": "healthy"})
```

### Monitoring Tools
- **Uptime:** UptimeRobot, Pingdom
- **Errors:** Sentry
- **Performance:** New Relic, DataDog
- **Logs:** ELK Stack, CloudWatch

## Backup Strategy

### Firestore Backup
```bash
gcloud firestore export gs://your-backup-bucket
```

### Automated Daily Backups
```bash
# Cron job
0 2 * * * /usr/local/bin/backup_firestore.sh
```

## Scaling

### Horizontal Scaling
- Multiple Gunicorn workers
- Load balancer (Nginx, HAProxy)
- Multiple server instances

### Caching Layer
```python
# Install Redis
pip install redis django-redis

# settings.py
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}
```

## Troubleshooting

### Common Issues

#### 1. 502 Bad Gateway
- Check Gunicorn is running: `sudo supervisorctl status`
- Check logs: `tail -f /var/log/payme_backend/gunicorn.err.log`

#### 2. Static Files Not Loading
- Run collectstatic: `python manage.py collectstatic`
- Check Nginx static path configuration

#### 3. Firebase Connection Issues
- Verify service account JSON file exists
- Check file permissions
- Verify Firestore API enabled

#### 4. Payme Webhook Failures
- Verify IP whitelist configured
- Check Basic Auth credentials
- Review webhook logs

## Maintenance

### Regular Tasks
- [ ] Monitor error logs daily
- [ ] Check disk space weekly
- [ ] Update dependencies monthly
- [ ] Review security patches
- [ ] Backup verification

### Updates
```bash
# Activate virtual environment
source venv/bin/activate

# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Migrate database
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo supervisorctl restart payme_backend
```

## Support

### Getting Help
- Check logs: `tail -f logs/payme_backend.log`
- Django errors: `python manage.py check`
- Deployment check: `python manage.py check --deploy`

---

*Last Updated: 2026-07-04*
