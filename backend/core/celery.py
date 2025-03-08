from __future__ import absolute_import, unicode_literals
from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Define exchanges
default_exchange = Exchange('default', type='direct')
user_exchange = Exchange('users', type='topic')

# Define queues
app.conf.task_queues = (
    Queue('default', default_exchange, routing_key='default'),
    Queue('users', user_exchange, routing_key='users.#'),
)

# Update Celery configuration
app.conf.update(
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
    task_track_started=True,
    task_time_limit=1800,
    task_soft_time_limit=1700,
    result_backend='redis://127.0.0.1:6379/0',
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_create_missing_queues=True,
)

# Task routing
# app.conf.task_routes = {
#     'translator.tasks.*': {
#         'queue': 'users',
#         'exchange': 'users',
#         'routing_key': 'users.tasks'
#     }
# }

# Task routing
app.conf.task_routes = {
    'translator.tasks.*': {
        'queue': lambda task, args, kwargs: (
            f'user.{kwargs["book_id"]}' if 'book_id' in kwargs
            else 'default'
        )
    }
}

# Periodic tasks
app.conf.beat_schedule = {
    'check-stuck-books': {
        'task': 'translator.tasks.check_stuck_books',
        'schedule': crontab(minute='*/10'),
        'options': {'queue': 'default'}
    },
}

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')