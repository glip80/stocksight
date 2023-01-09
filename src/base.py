import os
from django import setup
# replace project_name with your own project name
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
setup()

# import os
from django.core.wsgi import get_wsgi_application
# os.environ.setdefault("DJANGO_SETTINGSS_MODULE", "<settings_file_path>")
application = get_wsgi_application()


from data.models import *