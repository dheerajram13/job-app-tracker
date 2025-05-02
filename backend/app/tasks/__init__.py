from celery import Celery

# Configure Celery
app = Celery(
    'tasks',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0',
    include=['app.tasks.job_scraper']
)

# Configure task execution
app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_concurrency=4,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=270,  # 4.5 minutes
    broker_connection_retry=True,
    broker_connection_max_retries=10
)

# Create periodic tasks schedule
from celery.schedules import crontab

from datetime import timedelta

app.conf.beat_schedule = {
    'periodic-job-scraping': {
        'task': 'app.tasks.job_scraper.periodic_scrape_jobs',
        'schedule': timedelta(hours=3),  # Run every 3 hours
        'args': (
            # Default search parameters
            [
                "Software Engineer",
                "Full Stack Developer",
                "Backend Developer",
                "Frontend Developer"
            ],
            "Australia",
            100,
            ["linkedin", "indeed"],  # Default job boards
            24,  # Last 24 hours
            True  # Fetch descriptions
        )
    }
}
