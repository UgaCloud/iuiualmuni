#!/usr/bin/env python3
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iuiualumni.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Set superuser credentials
email = "admin@iuiuaa.com"
full_name = "Administrator"
password = "Admin#1334"

# Check if superuser already exists
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email, full_name=full_name, password=password)
    print(f"Superuser '{email}' created successfully!")
else:
    print(f"Superuser '{email}' already exists.")
