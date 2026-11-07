import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("inovatx_core")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks(["core"])

app.conf.task_acks_late = True
app.conf.task_default_retry_delay = 60
app.conf.task_reject_on_worker_lost = True


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
