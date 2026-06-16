#!/usr/bin/env bash
pip install -r requirements.txt
python manage.py migrate
python manage.py shell -c "
from django.contrib.auth.models import User
import os
if not User.objects.filter(username='Zaman').exists():
    User.objects.create_superuser('Zaman', 'sabina.zaman@gmail.com', os.environ.get('SUPERUSER_PASSWORD'))
    print('Superuser created')
else:
    print('Superuser already exists')
"
