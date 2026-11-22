# State shared across instances needs Redis, with no in-memory fallback

Rate limiting and realtime fan-out (WebSockets, server-sent events) must see
every instance's counters and messages. Rather than keep them in memory and
switch to Redis when it happens to be present, which looks right on one
instance and silently breaks on two, ticking either option makes Redis a needed
option: one shared `redis` service and `REDIS_URL`. Tests use fakeredis, so the
cost is one container in development, not a test dependency on a server.
