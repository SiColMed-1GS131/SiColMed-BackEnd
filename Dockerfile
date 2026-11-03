FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuario sin privilegios. La carpeta de uploads se crea aquí con su dueño para
# que el volumen `uploads` herede esos permisos la primera vez que se monta.
RUN useradd -m appuser \
    && mkdir -p /data/uploads \
    && chown appuser /data/uploads
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]