# Obtenemos la imagen
FROM python:latest

# Directorio de trabajo
WORKDIR /app

# Creamos un archivo llamado secrets.toml en la carpeta /app/.streamlit
RUN mkdir /app/.streamlit
RUN echo "DROPBOX_KEY = 'fa2akhrevjkz1qy'\nDROPBOX_SECRET = 'njz7lm1jh0rbrwd'\nDROPBOX_TOKEN = ''" > /app/.streamlit/secrets.toml

# Creamos la carpeta de datos para dropbox
RUN mkdir /app/data/Dropbox

# Instalamos las dependencias
RUN  python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

# Exponemos el puerto
EXPOSE 8501
CMD [ "streamlit", "run", "app.py"]

