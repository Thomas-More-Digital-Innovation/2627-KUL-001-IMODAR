FROM python:3.13-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

FROM python:3.13-slim
WORKDIR /app
# The package runs from /app; matplotlib needs a writable cache on a read-only root filesystem.
ENV PATH=/app/.venv/bin:$PATH PYTHONPATH=/app PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/matplotlib
COPY --from=build /app/.venv .venv
COPY alembic.ini ./
COPY migrations migrations
COPY imodar imodar
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "imodar.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
