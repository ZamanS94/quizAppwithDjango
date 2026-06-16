#!/usr/bin/env bash
pip install -r requirements.txt
python manage.py migrate
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('Zaman', 'sabina.zaman@gmail.com', 'sN&071158')
    print('Superuser created')
else:
    print('Superuser already exists')
"