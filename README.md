# LabCore API

Base URL: `http://localhost:8000`
Porta: http://localhost:52773/csp/sys/UtilHome.csp

## Running locally

```bash
docker compose up --build
```

## Database connection (DBeaver)

JDBC URL: `jdbc:IRIS://localhost:1972/USER`

| Setting   | Value      |
|-----------|------------|
| Host      | localhost  |
| Port      | 1972       |
| Namespace | USER       |
| Username  | _SYSTEM    |
| Password  | SYS        |

Tables are created under the `labcore` schema:
`patient`, `practitioner`, `service_request`, `service_request_item`, `exam_catalog`

## Generated API docs

FastAPI also exposes the generated API documentation at:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`
- `http://localhost:8000/openapi.json`
