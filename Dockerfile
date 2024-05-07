# Obtenemos la imagen
FROM python:3.12

# Directorio de trabajo
WORKDIR /app
# Clonamos el repositorio
RUN git clone https://github.com/xd-mau5/zomac_data.git
# Movemos los archivos
RUN mv zomac_data/* /app
# Eliminamos el directorio
RUN rm -rf zomac_data

# Creamos un archivo llamado secrets.toml en la carpeta /app/.streamlit
RUN mkdir /app/.streamlit
RUN echo "DROPBOX_KEY = 'fa2akhrevjkz1qy'\nDROPBOX_SECRET = 'njz7lm1jh0rbrwd'\nDROPBOX_TOKEN = 'sl.B0wfPA_yOwwI2FCIFQ7TMjVhA3a2zoHb78_smMK-AcIgAPLKQHM28eqtW51WMrVW6jucrqKCEJUKXJ1S-CETQcTDYUex744GiSzFfZVW_jLyneKuFfLeZSHQc8qc2WWBdycRCa-8kF1xDbQs4w90aJM'" > /app/.streamlit/secrets.toml

# Creamos la carpeta de datos para dropbox
RUN mkdir /app/data/Dropbox

# Instalamos las dependencias
RUN  python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

# Exponemos el puerto
EXPOSE 8501
EXPOSE 80
# Ejecutamos el comando para correr la app
CMD [ "streamlit", "run", "app.py" ,"--server.port", "80"]

