# Título del Proyecto

Dashboard de Analítica de Datos de producción en Tropical Food Export S.A.S.

## Comenzando

1. Clonar el repositorio
```bash
git clone https://github.com/xd-mau5/zomac_data.git
```
2. Crear un entorno virtual
```bash
python -m venv venv
```
3. Activar el entorno virtual
```bash
source venv/bin/activate
```
- En Windows
```bash
venv\Scripts\activate.bat
venv\Scripts\activate.ps1
```
4. Instalar las dependencias
```bash
pip install -r requirements.txt
```
5. Crear un archivo .env en la raíz del proyecto con las siguientes variables de entorno abriendo el [panel de control de Dropbox](https://www.dropbox.com/developers/apps) y creando una nueva aplicación

```bash
DROPBOX_KEY=your_dropbox_key
DROPBOX_SECRET=your_dropbox_secret
DROPBOX_TOKEN=your_dropbox_token
```
6. Se deben marcar los siguientes permisos en la aplicación de Dropbox

✅ **files.content.read**

7. Descargar los datos faltantes de la carpeta de Dropbox
```bash
python download_data.py
```
8. Correr el servidor
```bash
streamlit run app.py
```

### Prerequisitos

- Python 3.8 o superior
- pip
- git
