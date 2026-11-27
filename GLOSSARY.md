# moarch-py

A CLI that scaffolds and grows modular-monolith FastAPI projects. These are the
words it uses for what a generated project can have.

## Project shape

**Module**:
One business area of a generated project, with its own layers and a `public.py`
that is the only thing other modules may import.
_Avoid_: Feature (kept only as a hidden alias), app, domain

**Checklist option**:
One thing `init` can generate, ticked or not, that a project either has or does not.
_Avoid_: Flag, feature toggle, add-on

**Preset**:
A kind of app `init` can start from; it only pre-ticks and locks checklist
options and is never recorded in the project.
_Avoid_: Template, project type, profile

**Checklist**:
One titled group of checklist options in the `init` wizard: What to generate,
Auth, Security, Background & realtime, Services, Observability.
_Avoid_: Section, step, page

**Required option**:
A checklist option a preset locks on, because that kind of app cannot do without it.
_Avoid_: Mandatory, forced option

**Anchor**:
A `# moarch:<name>` comment in a generated file, marking where `moarch-py`
adds lines later; the owner keeps it when editing around it.
_Avoid_: Marker, hook, placeholder

**Needed option**:
A checklist option ticked automatically because another ticked option cannot
work without it, shown as "(needed by …)".
_Avoid_: Dependency, prerequisite, implied option

## Auth

**Access token**:
A short-lived token a client sends on every request to say who it is.
_Avoid_: JWT, bearer, session token

**Refresh token**:
A long-lived, single-use token a client trades for a new access token and a new
refresh token.
_Avoid_: Long token, renew token

**Token reuse**:
A refresh token presented after it was already traded, taken as a sign of theft.
_Avoid_: Replay, double refresh

**Social sign-in**:
Signing in with a Google or Apple account, where the client proves the account
and the backend issues its own tokens.
_Avoid_: OAuth login, SSO, third-party auth

**Linked identity**:
One Google or Apple account attached to a user, known by the provider's own ID
for that account; a user can have several.
_Avoid_: Social account, provider account, connection

**Password policy**:
The rules a new password must meet (length, and whether symbols, numbers or
capitals are demanded), set per project.
_Avoid_: Password rules, complexity rules

**Lockout**:
A temporary refusal of sign-in to one user from one client after too many
failed attempts from it, or from every client once the account-wide ceiling
is reached.
_Avoid_: Ban, suspension

**Block**:
One user hiding another: neither sees what the other publishes or can reach them.
_Avoid_: Mute, ban

**Report**:
A user's complaint about another user or about something users published,
waiting for review.
_Avoid_: Flag, complaint

**Entitlement**:
What a verified store purchase gives a user: one product, one purchase, one account.
_Avoid_: License, subscription, unlock

**Verified user**:
A user who has proved they own their email address.
_Avoid_: Confirmed, active, activated user

## Background and realtime

**Broker**:
The message server that carries background tasks between the API and the
worker: RabbitMQ, Redis, or none.
_Avoid_: Queue, message bus, MQ

**Task**:
A unit of background work the API hands off and a worker runs later.
_Avoid_: Job, background job, celery task

**Scheduled task**:
A task the scheduler puts on the broker at fixed times, such as a nightly cleanup.
_Avoid_: Cron job, periodic job

**Worker**:
The separate process that runs tasks taken from the broker.
_Avoid_: Consumer, runner, daemon

## Security

**Audit log**:
An append-only record of who did what to which record, and when.
_Avoid_: Activity log, history, event log

**Idempotency key**:
A client-chosen value on a write request so that retrying it does the work only once.
_Avoid_: Request ID, dedupe key

## Observability

**Telemetry**:
What a running project reports about itself so the people operating it can see
what it did: log lines, traces and metrics.
_Avoid_: Events, monitoring data, analytics

**Request ID**:
The ID that ties together every log line, trace and task one request caused,
taken from the caller when it sends a well-formed one.
_Avoid_: Correlation ID, trace ID
