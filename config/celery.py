import os

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.update(worker_hijack_root_logger=False)  # prevent Celery from duplicating logs
app.autodiscover_tasks()
