"""
Celery worker for background settlement processing.

In Phase 1 (pure simulator), the admin /advance endpoint handles
settlement synchronously. This worker is the foundation for Phase 3
async realism — tasks are defined here and can be triggered by
the API or by chaining.
"""

from celery import Celery

from app.config import settings

celery = Celery(
    "cross_border_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)


@celery.task(name="process_transfer_step")
def process_transfer_step(transfer_id: str):
    """
    Placeholder task — in Phase 3 this will:
    1. Load the transfer from DB (sync session)
    2. Call the next settlement step
    3. Schedule the following step
    """
    return {"transfer_id": transfer_id, "status": "stub — use /admin/advance for now"}
