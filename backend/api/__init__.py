from django.conf import settings
def log(msg):
    if settings.DEBUG:
        print(msg)