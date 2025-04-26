# Dockerfile for doctrace-ai

# 1. Imagen base oficial de Python
FROM python:3.12-slim

# 2. Directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar el resto de la aplicación
COPY . .

# 5. Exponer el puerto que usará FastAPI
EXPOSE 8000

# 6. Comando por defecto para arrancar la app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]