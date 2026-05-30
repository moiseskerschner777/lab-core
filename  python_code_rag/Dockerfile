FROM python:3.12-slim
WORKDIR /python-code-rag
COPY pyproject.toml .
RUN pip install -e .
COPY app/ app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
