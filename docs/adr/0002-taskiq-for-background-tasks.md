# Background tasks run on taskiq, with RabbitMQ or Redis as the broker

Generated projects use taskiq rather than Celery, arq or Dramatiq. It is
async-native, so tasks share the app's `async def` style and async SQLAlchemy
sessions, and it supports both RabbitMQ (aio-pika) and Redis, which lets the
broker be a choice like the database. Celery, the familiar option, is sync at its
core; arq is Redis-only.
