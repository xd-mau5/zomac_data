# Obtenemos la imagen
FROM python:latest

# Directorio de trabajo
WORKDIR /app

RUN git clone https://github.com/xd-mau5/zomac_data.git
# Movemos los archivos
RUN mv zomac_data/* /app
# Eliminamos el directorio
RUN rm -rf zomac_data

# Creamos un archivo llamado secrets.toml en la carpeta /app/.streamlit
RUN mkdir /app/.streamlit
RUN echo "DROPBOX_KEY = 'fa2akhrevjkz1qy'\nDROPBOX_SECRET = 'njz7lm1jh0rbrwd'\nDROPBOX_TOKEN = ''" > /app/.streamlit/secrets.toml

# Creamos la carpeta de datos para dropbox
RUN mkdir /app/data/Dropbox

# Instalamos las dependencias
RUN  python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

# Exponemos el puerto 8080
EXPOSE 8080
CMD [ "streamlit", "run", "app.py"]

# Construimos la imagen
# docker build -t tropical_data .
# Bindeamos el puerto 8080
# docker run -p 8080:8080 tropical_data