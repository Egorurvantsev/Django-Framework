import os

from celery import Celery

# Устанавливаем настройки Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Создаём экземпляр Celery
celery_app = Celery("mmkndr")

# Загружаем конфигурацию из настроек Django с префиксом 'CELERY'
celery_app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически обнаруживаем задачи в приложениях
celery_app.autodiscover_tasks()
