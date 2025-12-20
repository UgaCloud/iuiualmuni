#!/home2/iuiuaaor/virtualenv/public_html/main/3.13/bin/python
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iuiualumni.settings")
django.setup()

from django.core.management import call_command

call_command("collectstatic", interactive=False, clear=True)
print("✅ collectstatic complete")
