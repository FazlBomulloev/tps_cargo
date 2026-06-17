FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

CMD ["python", "-m", "src.main"]
