FROM python:3.11-slim AS build
WORKDIR /w
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

FROM python:3.11-slim
RUN useradd -m app
WORKDIR /app
COPY --from=build /install /usr/local
COPY src ./src
COPY config ./config
USER app
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request as u;u.urlopen('http://localhost:8000/healthz')"
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
