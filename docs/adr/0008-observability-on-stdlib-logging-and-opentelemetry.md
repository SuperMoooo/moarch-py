# Observability is stdlib logging plus OpenTelemetry; domain events are separate

Generated projects log through the standard library's `logging`, with a JSON
formatter written into the template and the request ID read from a
`contextvar`, and trace through OpenTelemetry. structlog was the obvious
alternative and has the nicer API, but it leaves a project with two logging
APIs and needs extra wiring to bring uvicorn's and every library's stdlib
records into the same format; python-json-logger would add a dependency for a
formatter of a few dozen lines. Logs are not exported over OpenTelemetry,
whose Python logs SDK is still experimental: they go to stdout, carrying the
trace ID so a line can be found in the trace view.

Kafka was asked about and left out on purpose. It carries domain events
(`OrderPlaced`) between modules or services, which is event-driven
architecture, not telemetry; it needs an outbox, a broker choice and a
contract for how modules publish, and gets its own design. Changing the
logging library later would touch every generated project's `logging.py`,
`main.py` and worker, which is why this is written down.
