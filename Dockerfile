# Obtenemos la imagen
FROM python:latest

# Directorio de trabajo
WORKDIR /app

COPY . .

# Instalamos las dependencias
RUN  python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

# Exponemos el puerto
EXPOSE 8501
CMD [ "streamlit", "run", "app.py"]

