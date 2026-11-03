FROM python:3.11-slim
RUN useradd -m -u 1000 user
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
COPY src ./src
COPY config ./config
USER user
EXPOSE 7860
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "7860"]
