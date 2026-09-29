# ---- Stage 1 : builder (installe les dependances) ----
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ---- Stage 2 : image finale ----
FROM python:3.12-slim
ARG APP_VERSION=dev
ENV APP_VERSION=$APP_VERSION
WORKDIR /app

RUN useradd --create-home appuser

COPY --from=builder /root/.local /home/appuser/.local
COPY . .

RUN chown -R appuser:appuser /app /home/appuser/.local
USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
