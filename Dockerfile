FROM python:3.12-slim

WORKDIR /app

# Copiar arquivos
COPY public/ public/
COPY app.py .
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir flask

# Expor porta
EXPOSE 8080

# Rodar Flask
CMD ["python", "app.py"]
