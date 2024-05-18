import dropbox.exceptions
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import dropbox
import dropbox.files
import dropbox.oauth

KEY = st.secrets["DROPBOX_KEY"]
SECRET = st.secrets["DROPBOX_SECRET"]
TOKEN = st.secrets["DROPBOX_TOKEN"]
folder_data_dropbox = r"data/Dropbox"

st.set_page_config(
    page_title="Analisis de datos de Tropical Food Export SAS",
    page_icon="🍌",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': """
        Esta aplicación permite analizar los datos de la empresa Tropical Food Export SAS.

        En la parte izquierda se encuentra el menú de opciones, donde se puede seleccionar la opción deseada.
        """
    }
)
colores_embolse = pd.read_csv('data/colores_semana_embolse.csv')
colores_desflore = pd.read_csv('data/colores_semana_desflore.csv')
lotes_finca = pd.read_csv('data/lotes.csv')

# Diccionarios con informacion de fincas y lotes
fincas = {
    'San Pedro': ['S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S07', 'S08', 'S09'],
    'Uveros' : ['U06', 'U07', 'E21'],
    'Damaquiel': ['D08', 'D09', 'D10', 'D11', 'D20'],
    'Pedrito': ['P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10', 'P11', 'P12', 'P13', 'P14', 'PN20', 'P15', 'P20'],
    'Montañita': ['M01', 'M02', 'M03', 'M04', 'M05', 'M07']
    }

#st.write("# Analisis de datos de Tropical Food Export SAS")
st.title("Analisis de datos de Tropical Food Export SAS")

paginas = ['Autenticacion en Dropbox',
           'Graficos de Produccion',
           'Graficos Semanales',
           'Tareas Periodicas']

def dropbox_oauth():
    flow = dropbox.DropboxOAuth2FlowNoRedirect(KEY, SECRET, token_access_type="legacy", locale="es-419")
    authorize_url = flow.start()
    st.write("Ir a la siguiente URL para autorizar la aplicación:")
    st.link_button("Ir a la página de autorización", authorize_url)
    auth_code = st.text_input("Ingrese el código de autorización aquí: ", key='5221154').strip()
    try:
        oauth_result = flow.finish(auth_code)
    except Exception as e:
        print("Error: %s" % (e,))
        return
    st.code(str(oauth_result.access_token), language="textfile")
    return oauth_result.access_token

def change_token_secrets():
    new_secret = ""
    # Modificamos el archivo de secretos, es un TOML, leerlo y modificar la linea que contiene el token
    while new_secret == "":
        try:
            new_secret = st.text_input("Ingrese el nuevo token secreto: ").strip()
        except Exception as e:
            pass
    with open(".streamlit/secrets.toml", "r") as f:
        lines = f.readlines()
    with open(".streamlit/secrets.toml", "w") as f:
        for line in lines:
            if "DROPBOX_TOKEN" in line:
                f.write(f'DROPBOX_TOKEN = "{new_secret}"\n')
                st.success("Token secreto modificado con exito")
            else:
                f.write(line)
            
def files_download(dbx: dropbox.Dropbox, folder: str, file: str, remote_folder: str):
    with open(os.path.join(folder, file), "wb") as f:
        metadata, res = dbx.files_download(remote_folder + "/" + file)
        f.write(res.content)

def search_excel_rdt(dbx: dropbox.Dropbox, folder: str, remote_folder: str):
    for entry in dbx.files_list_folder(remote_folder).entries:
        if entry.name.endswith(".xlsx") and entry.name.startswith("RDT"):
            files_download(dbx, folder, entry.name, remote_folder)
            if entry.name.endswith(".xlsx") and entry.name.startswith("RDT"):
                return entry.name

def search_excel_embarque(dbx: dropbox.Dropbox, folder: str, remote_folder: str):
    for entry in dbx.files_list_folder(remote_folder).entries:
        if entry.name.endswith(".xlsx") and "EMBARQUE" in entry.name:
            files_download(dbx, folder, entry.name, remote_folder)
            if entry.name.endswith(".xlsx") and "EMBARQUE" in entry.name:
                return entry.name
            
@st.cache_data(ttl='12h')
def procesamiento_datos_embarque():
    # Listar los archivos en la carpeta 'data/Dropbox'
    archivos = os.listdir('data/Dropbox')
    # Buscar el archivo de EMBARQUE
    for archivo in archivos:
        if "EMBARQUE" in archivo:
            embarque = archivo
    sheet = 'CALCULO PAGO'
    df = pd.read_excel(r'data/Dropbox/' + embarque, sheet_name=sheet)
    df = df.iloc[6:, 2:]
    df.columns = df.iloc[0]
    df = df.iloc[1:]
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    # Convertimos la fecha al formato 'DD/MM/YYYY'
    df['Fecha'] = df['Fecha'].dt.strftime('%d/%m/%Y')
    # Creamos la columna 'Cajas por Hectarea' y la llenamos con ceros
    df['Cajas por Hectarea'] = 0
    # La colocamos como tipo float
    df['Cajas por Hectarea'] = df['Cajas por Hectarea'].astype(float)
    # Creamos la columna 'Bolsas por Hectarea' y la llenamos con ceros
    df['Bolsas por Hectarea'] = 0
    # La colocamos como tipo float
    df['Bolsas por Hectarea'] = df['Bolsas por Hectarea'].astype(float)
    # Sacando los datos de 'data/total_hectareas_por_finca.csv' se creara una nueva columna en el dataframe de embarque tomando en cuenta la finca, el area neta y la cantidad de cajas
    total_hectareas = pd.read_csv('data/total_hectareas_por_finca.csv')
    for index, row in df.iterrows():
        for index2, row2 in total_hectareas.iterrows():
            if row['Finca'] == row2['Finca']:
                df.at[index, 'Cajas por Hectarea'] = row['Cajas'] / row2['Tamaño Area Neta']
    # Hacemos lo mismo pero con la columna 'Bolsas'
    for index, row in df.iterrows():
        for index2, row2 in total_hectareas.iterrows():
            if row['Finca'] == row2['Finca']:
                df.at[index, 'Bolsas por Hectarea'] = row['Bolsas'] / row2['Tamaño Area Neta']
    # Eliminamos las filas que tengan el Año = 2021
    df = df.drop(df[df['Año'] == 2021].index)
    # Colocar fecha en tipo datetime
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y')
    # Eliminar las filas donde la 'Finca' sea igual a 0
    df = df[df['Finca'] != 0]
    df_agrupado = df.groupby(['Finca', 'Año', 'Semana']).sum(numeric_only=True).reset_index()
    return df_agrupado

@st.cache_data(ttl='12h')
def procesamiento_datos_embarque_cajas():
    # Listar los archivos en la carpeta 'data/Dropbox'
    archivos = os.listdir('data/Dropbox')
    # Buscar el archivo de EMBARQUE
    for archivo in archivos:
        if "EMBARQUE" in archivo and not archivo.startswith('~$'):
            embarque = archivo
    sheet = 'CALCULO PAGO'
    df = pd.read_excel(r'data/Dropbox/' + embarque, sheet_name=sheet)
    df = df.iloc[6:, 2:]
    df.columns = df.iloc[0]
    df = df.iloc[1:]
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    # Convertimos la fecha al formato 'DD/MM/YYYY'
    df['Fecha'] = df['Fecha'].dt.strftime('%d/%m/%Y')
    df.reset_index(drop=True, inplace=True)
    columnas_a_conservar = ['Fecha', 'Año', 'Semana', 'Cajas', 'Finca', 'Total Racimos', 'Ratio', 'Bolsas']
    df = df[columnas_a_conservar]
    # Eliminamos las filas que en Cajas tengan un valor NaN
    df = df.dropna(subset=['Cajas']).reset_index(drop=True)
    df = df.groupby(['Año', 'Semana', 'Finca']).sum().reset_index()
    df.drop(columns=['Fecha'], inplace=True)
    df['Año'] = df['Año'].astype(int)
    df['Semana'] = df['Semana'].astype(int)
    df['Cajas'] = df['Cajas'].astype(int)
    df['Total Racimos'] = df['Total Racimos'].astype(int)
    df['Ratio'] = df['Ratio'].astype(float)
    df['Bolsas'] = df['Bolsas'].astype(float)
    return df

@st.cache_data(ttl='12h')
def procesamiento_datos_sioma_embolse():
    df = pd.read_excel(r'data/Sioma/embolse.xlsx')
    # Agregamos la columna de Año y Semana
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y-%m-%d %H:%M:%S')
    df['Año'] = df['Fecha'].dt.year
    df['Semana'] = df['Fecha'].dt.isocalendar().week
    df['Finca'] = ''
    # Usando la informacion del diccionario fincas, si un lote dentro del dataframe esta en uno de los values de finca, colocar la key en la columna finca
    for index, row in df.iterrows():
        for key, value in fincas.items():
            if row['Lote'] in value:
                df.at[index, 'Finca'] = key
    df = df.dropna(subset=['Lote'])
    df = df.rename(columns={'Tipo de labor': 'Color'})
    df = df[df['Finca'] != '']
    color = pd.read_csv('data/colores_semana_embolse.csv')
    df['Codigo Color'] = df['Color'].map(dict(zip(color['Color'], color['Codigo Color'])))
    return df

@st.cache_data(ttl='12h')
def procesamiento_datos_embarque_ratio():
    # Listar los archivos en la carpeta 'data/Dropbox'
    archivos = os.listdir('data/Dropbox')
    # Buscar el archivo de EMBARQUE
    for archivo in archivos:
        if "EMBARQUE" in archivo and not archivo.startswith('~$'):
            embarque = archivo
    sheet = 'CALCULO PAGO'
    df = pd.read_excel(r'data/Dropbox/' + embarque, sheet_name=sheet)
    df = df.iloc[6:, 2:]
    df.columns = df.iloc[0]
    df = df.iloc[1:]
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    # Convertimos la fecha al formato 'DD/MM/YYYY'
    df['Fecha'] = df['Fecha'].dt.strftime('%d/%m/%Y')
    df.reset_index(drop=True, inplace=True)
    columnas_a_conservar = ['Fecha', 'Año', 'Semana', 'Cajas', 'Finca', 'Total Racimos', 'Ratio', 'Bolsas']
    df = df[columnas_a_conservar]
    # Eliminamos las filas que en Cajas tengan un valor NaN
    df = df.dropna(subset=['Cajas']).reset_index(drop=True)
    df = df.groupby(['Año', 'Semana', 'Finca']).sum().reset_index()
    df.drop(columns=['Fecha'], inplace=True)
    df['Año'] = df['Año'].astype(int)
    df['Semana'] = df['Semana'].astype(int)
    df['Cajas'] = df['Cajas'].astype(int)
    df['Total Racimos'] = df['Total Racimos'].astype(int)
    df['Ratio'] = df['Ratio'].astype(float)
    df['Bolsas'] = df['Bolsas'].astype(float)
    df['Ratio'] = df['Total Racimos'] / df['Cajas']
    return df

@st.cache_data(ttl='12h')
def procesamiento_datos_embarque_ratio_inverso():
    # Listar los archivos en la carpeta 'data/Dropbox'
    archivos = os.listdir('data/Dropbox')
    # Buscar el archivo de EMBARQUE
    for archivo in archivos:
        if "EMBARQUE" in archivo and not archivo.startswith('~$'):
            embarque = archivo
    sheet = 'CALCULO PAGO'
    df = pd.read_excel(r'data/Dropbox/' + embarque, sheet_name=sheet)
    df = df.iloc[6:, 2:]
    df.columns = df.iloc[0]
    df = df.iloc[1:]
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    # Convertimos la fecha al formato 'DD/MM/YYYY'
    df['Fecha'] = df['Fecha'].dt.strftime('%d/%m/%Y')
    df.reset_index(drop=True, inplace=True)
    columnas_a_conservar = ['Fecha', 'Año', 'Semana', 'Cajas', 'Finca', 'Total Racimos', 'Ratio', 'Bolsas']
    df = df[columnas_a_conservar]
    # Eliminamos las filas que en Cajas tengan un valor NaN
    df = df.dropna(subset=['Cajas']).reset_index(drop=True)
    df = df.groupby(['Año', 'Semana', 'Finca']).sum().reset_index()
    df.drop(columns=['Fecha'], inplace=True)
    df['Año'] = df['Año'].astype(int)
    df['Semana'] = df['Semana'].astype(int)
    df['Cajas'] = df['Cajas'].astype(int)
    df['Total Racimos'] = df['Total Racimos'].astype(int)
    df['Ratio'] = df['Ratio'].astype(float)
    df['Bolsas'] = df['Bolsas'].astype(float)
    df['Ratio'] = df['Cajas'] / df['Total Racimos']
    return df

@st.cache_data(ttl='12h')
def procesamiento_datos_sioma_corte():
    df = pd.read_excel(r'data/Sioma/corte.xlsx')
    # Agregamos la columna de Año y Semana
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y-%m-%d %H:%M:%S')
    df['Año'] = df['Fecha'].dt.year
    df['Semana'] = df['Fecha'].dt.isocalendar().week
    df['Finca'] = ''
    # Usando la informacion del diccionario fincas, si un lote dentro del dataframe esta en uno de los values de finca, colocar la key en la columna finca
    for index, row in df.iterrows():
        for key, value in fincas.items():
            if row['Lote'] in value:
                df.at[index, 'Finca'] = key
    df = df.dropna(subset=['Lote'])
    df = df.rename(columns={'Tipo de labor': 'Color'})
    df = df[df['Finca'] != '']
    color = pd.read_csv('data/colores_semana_embolse.csv')
    df['Codigo Color'] = df['Color'].map(dict(zip(color['Color'], color['Codigo Color'])))
    return df

@st.cache_data(ttl='12h')
def procesamiento_datos_sioma_repique():
    df = pd.read_excel(r'data/Sioma/repique.xlsx')
    # Agregamos la columna de Año y Semana
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y-%m-%d %H:%M:%S')
    df['Año'] = df['Fecha'].dt.year
    df['Semana'] = df['Fecha'].dt.isocalendar().week
    df['Finca'] = ''
    # Usando la informacion del diccionario fincas, si un lote dentro del dataframe esta en uno de los values de finca, colocar la key en la columna finca
    for index, row in df.iterrows():
        for key, value in fincas.items():
            if row['Lote'] in value:
                df.at[index, 'Finca'] = key
    df = df.dropna(subset=['Lote'])
    df = df.rename(columns={'Tipo de labor': 'Color'})
    df = df[df['Finca'] != '']
    color = pd.read_csv('data/colores_semana_embolse.csv')
    df['Codigo Color'] = df['Color'].map(dict(zip(color['Color'], color['Codigo Color'])))
    return df

@st.cache_data(ttl='12h')
def procesamiento_datos_sioma_desflore():
    df = pd.read_excel(r'data/Sioma/desflore.xlsx')
    # Agregamos la columna de Año y Semana
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y-%m-%d %H:%M:%S')
    df['Año'] = df['Fecha'].dt.year
    df['Semana'] = df['Fecha'].dt.isocalendar().week
    df['Finca'] = ''
    # Usando la informacion del diccionario fincas, si un lote dentro del dataframe esta en uno de los values de finca, colocar la key en la columna finca
    for index, row in df.iterrows():
        for key, value in fincas.items():
            if row['Lote'] in value:
                df.at[index, 'Finca'] = key
    df = df.dropna(subset=['Lote'])
    df = df.rename(columns={'Tipo de labor': 'Color'})
    df = df[df['Finca'] != '']
    color = pd.read_csv('data/colores_semana_desflore.csv')
    df['Codigo Color'] = df['Color'].map(dict(zip(color['Color'], color['Codigo Color'])))
    return df

@st.cache_data(ttl='12h')
def procesamiento_datos_sioma_resiembra():
    df = pd.read_excel(r'data/Sioma/resiembra.xlsx')
    # Agregamos la columna de Año y Semana
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y-%m-%d %H:%M:%S')
    df['Año'] = df['Fecha'].dt.year
    df['Semana'] = df['Fecha'].dt.isocalendar().week
    df['Finca'] = ''
    # Usando la informacion del diccionario fincas, si un lote dentro del dataframe esta en uno de los values de finca, colocar la key en la columna finca
    for index, row in df.iterrows():
        for key, value in fincas.items():
            if row['Lote'] in value:
                df.at[index, 'Finca'] = key
    df = df.dropna(subset=['Lote'])
    df = df[df['Finca'] != '']
    return df

def procesamiento_datos_sioma_coco():
    df = pd.read_excel(r'data/Sioma/coco.xlsx')
    # Agregamos la columna de Año y Semana
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y-%m-%d %H:%M:%S')
    df['Año'] = df['Fecha'].dt.year
    df['Semana'] = df['Fecha'].dt.isocalendar().week
    df['Finca'] = ''
    # Usando la informacion del diccionario fincas, si un lote dentro del dataframe esta en uno de los values de finca, colocar la key en la columna finca
    for index, row in df.iterrows():
        for key, value in fincas.items():
            if row['Lote'] in value:
                df.at[index, 'Finca'] = key
    df = df.dropna(subset=['Lote'])
    df = df[df['Finca'] != '']
    return df

@st.cache_data(ttl='12h')
def procesamiento_datos_rdt():
    # Listar los archivos en la carpeta 'data/Dropbox'
    archivos = os.listdir('data/Dropbox')
    # Buscar el archivo de RDT
    for archivo in archivos:
        if archivo.startswith('RDT'):
            rdt = archivo
    # Leer el archivo de RDT
    df = pd.read_excel(r'data/Dropbox/' + rdt, sheet_name='RDT')
    # Eliminamos las primeras 13 filas y la primera columna
    df = df.iloc[13:, 1:]
    # Colocamos la primera fila como titulos de las columnas
    df.columns = df.iloc[0]
    df = df.iloc[1:]
    # Eliminamos las ultimas 4 columnas
    df = df.iloc[:, :-4]
    # Vamos a especificar las columnas que queremos conservar
    columnas_a_conservar = [
        'Fecha',
        'Año',
        'Semana',
        'Nombre Labor',
        ' Unides Primer Lote',
        'Codgo generico L1',
        'Unides Segundo Lote',
        'Codgo generico L 2',
        'Unides Tercer Lote',
        'Codgo generico L3',
        'Unides Cuarto Lote',
        'Codgo generico L4',
        'Labores'
        ]
    # Eliminamos las columnas que no estan en 'columnas_a_conservar'
    df = df[columnas_a_conservar]
    # Cambiamos el nombre de las columnas
    df.columns = [
        'Fecha',
        'Año',
        'Semana',
        'Nombre Labor',
        'Unidades Primer Lote',
        'Codigo Generico L1',
        'Unidades Segundo Lote',
        'Codigo Generico L2',
        'Unidades Tercer Lote',
        'Codigo Generico L3',
        'Unidades Cuarto Lote',
        'Codigo Generico L4',
        'Labores'
    ]
    # Eliminamos las filas donde 'Labores' sea igual a 0 y 'Nombre Labor' sea igual a 'No Trabajó', solamente si se cumplen estas dos condiciones
    df = df.drop(df[(df['Labores'] == 0) & (df['Nombre Labor'] == 'No Trabajó')].index)
    # Eliminamos las filas que tengan los valores de 'Nombre Labor' en 0 y 'Labores' en 0
    df = df.drop(df[(df['Nombre Labor'] == 0) & (df['Labores'] == 0)].index).reset_index(drop=True)
    # Vamos a cambiar el formato de la fecha a 'DD/MM/YYYY'
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df['Fecha'] = df['Fecha'].dt.strftime('%d/%m/%Y')
    # Eliminamos las filas donde 'Labores' sea igual a 0
    df = df.drop(df[df['Labores'] == 0].index).reset_index(drop=True)
    # Asginamos tipo de valor a las columnas
    #df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df['Año'] = df['Año'].astype(int)
    df['Semana'] = df['Semana'].astype(int)
    df['Nombre Labor'] = df['Nombre Labor'].astype(str)
    df['Labores'] = df['Labores'].astype(str)
    # Las unidades en tipo float con dos decimales
    df['Unidades Primer Lote'] = df['Unidades Primer Lote'].astype(float)
    df['Unidades Segundo Lote'] = df['Unidades Segundo Lote'].astype(float)
    df['Unidades Tercer Lote'] = df['Unidades Tercer Lote'].astype(float)
    df['Unidades Cuarto Lote'] = df['Unidades Cuarto Lote'].astype(float)
    # Los codigos en tipo string
    df['Codigo Generico L1'] = df['Codigo Generico L1'].astype(str)
    df['Codigo Generico L2'] = df['Codigo Generico L2'].astype(str)
    df['Codigo Generico L3'] = df['Codigo Generico L3'].astype(str)
    df['Codigo Generico L4'] = df['Codigo Generico L4'].astype(str)
    # Colocamos los valores de 'Labores' en formato titulo
    df['Labores'] = df['Labores'].str.title()
    return df
    
def run():
    st.sidebar.title("Menu")
    pagina = st.sidebar.radio("Seleccionar pagina", paginas)

    if pagina == 'Autenticacion en Dropbox':
            try:
                dbx = dropbox.Dropbox(TOKEN)
                with st.spinner("Descargando archivos de Dropbox"):
                    dbx = dropbox.Dropbox(TOKEN)
                    # Buscar el archivo de RDT 
                    search_excel_rdt(dbx, folder_data_dropbox, '/TROPICAL  2022/Nomina Dopbox/RDT 2023')
                    st.success("RDT descargado")
                    # Buscar el archivo de EMBARQUE
                    search_excel_embarque(dbx, folder_data_dropbox, '/TROPICAL  2022/Embarque Dropbox')
                    st.success("Embarque descargado")
                    st.success("Archivos descargados con exito")
            except dropbox.exceptions.AuthError as e:
                print("Error: %s" % (e,))
                dropbox_oauth()
                change_token_secrets()
                dbx = dropbox.Dropbox(TOKEN)
                with st.spinner("Descargando archivos de Dropbox"):
                    dbx = dropbox.Dropbox(TOKEN)
                    # Buscar el archivo de RDT 
                    search_excel_rdt(dbx, folder_data_dropbox, '/TROPICAL  2022/Nomina Dopbox/RDT 2023')
                    st.success("RDT descargado")
                    # Buscar el archivo de EMBARQUE
                    search_excel_embarque(dbx, folder_data_dropbox, '/TROPICAL  2022/Embarque Dropbox')
                    st.success("Embarque descargado")
                    st.success("Archivos descargados con exito")
                st.success("Autenticación exitosa")
            except dropbox.exceptions.HttpError as e:
                print("Error: %s" % (e,))
            

    elif pagina == 'Graficos de Produccion':
        caja_por_hectarea, bacota_por_hectarea, ratio_de_produccion, ratio_de_produccion_inverso, bacota_lote_por_hectarea, bacota_lote, bacota_finca, cajas_finca = st.tabs(
            ["Caja por hectarea",
             "Bacota por hectarea",
             "Ratio de Producción",
             "Ratio de Producción Inverso",
             "Bacota por lote por hectarea",
             "Cantidad de Bacotas por lote",
             "Cantidad de Bacotas por finca",
             "Cantidad de Cajas por finca"
             ])
        with caja_por_hectarea.container():
            data = procesamiento_datos_embarque()
            st.subheader("Filtros para las graficas")
            finca_caja = data['Finca'].unique()
            year_caja = data['Año'].unique()
            finca, anio = st.columns(2)
            with finca:
                finca_seleccionada_cxh = st.radio("Seleccionar finca", finca_caja)
            with anio:
                anio_seleccionado_cxh = st.radio("Filtrar por año", year_caja, index=year_caja.size-1)
            # Filtrar por año
            data = data[data['Año'] == anio_seleccionado_cxh]
            # Filtrar por finca
            data = data[data['Finca'] == finca_seleccionada_cxh]
            fig = px.bar(data, x=data["Semana"], y=data['Cajas por Hectarea'],
                          title='Cajas por Hectarea', color='Cajas por Hectarea',
                          color_continuous_scale=px.colors.sequential.Bluered_r,
                          labels={'x': 'Semana', 'y': 'Cajas por hectarea'},
                          text_auto=True)
            fig.update_traces(texttemplate='%{y:.2f}', textposition='inside', hovertemplate='Semana: %{x}<br>Cajas por Hectarea: %{y}<br><extra></extra>')
            fig.update_xaxes(dtick=1)
            fig.update_yaxes(range=[0, data['Cajas por Hectarea'].max() + (data['Cajas por Hectarea'].max()/7)])
            st.plotly_chart(fig, use_container_width=True)
            
        with bacota_por_hectarea.container():
            data = procesamiento_datos_sioma_embolse()
            st.subheader("Filtros para las graficas")
            finca_bacota = data['Finca'].unique()
            year_bacota = data['Año'].unique()
            finca, anio = st.columns(2)
            total_hectareas = pd.read_csv('data/total_hectareas_por_finca.csv')
            with finca:
                finca_seleccionada_bxh = st.radio("Seleccionar finca", finca_bacota, key='sdasfadg')
            with anio:
                anio_seleccionado_bxh = st.radio("Filtrar por año", year_bacota, index=year_bacota.size-1, key='asdasd')
            # Filtrar por año
            temp = data[data['Año'] == anio_seleccionado_bxh]
            temp = temp.groupby(by='Semana')['Finca'].value_counts().unstack().fillna(0)
            temp = temp.reset_index()
            temp = temp.melt(id_vars='Semana', var_name='Finca', value_name='Cantidad')
            temp = temp[temp['Cantidad'] != 0]
            for index, row in temp.iterrows():
                for index2, row2 in total_hectareas.iterrows():
                    if row['Finca'] == row2['Finca']:
                        temp.at[index, 'Bacotas por Hectarea'] = row['Cantidad'] / row2['Tamaño Area Neta']
            # Filtrar por finca
            temp = temp[temp['Finca'] == finca_seleccionada_bxh]
            fig = px.bar(temp, x="Semana", y='Bacotas por Hectarea',
                          title='Bacotas por Hectarea', color='Bacotas por Hectarea',
                          color_continuous_scale=px.colors.sequential.Bluered_r,
                          labels={'x': 'Semana', 'y': 'Bacotas por hectarea'},
                          text_auto=True,
                          )
            fig.update_traces(texttemplate='%{y:.2f}', textposition='inside', hovertemplate='Semana: %{x}<br>Bacotas por Hectarea: %{y}<br><extra></extra>')
            fig.update_xaxes(dtick=1)
            fig.update_yaxes(range=[0, temp['Bacotas por Hectarea'].max() + (temp['Bacotas por Hectarea'].max()/7)])
            st.plotly_chart(fig, use_container_width=True)
        
        with ratio_de_produccion.container():
            data_embarque = procesamiento_datos_embarque_ratio()
            st.subheader("Filtros para las graficas")
            finca, anio = st.columns(2)
            with finca:
                finca_seleccionada_rdp = st.radio("Seleccionar finca", fincas.keys(), key='1714060469')
            with anio:
                anio_seleccionado_rdp = st.radio("Filtrar por año", data_embarque['Año'].unique(), key='1714060512', index=data_embarque['Año'].unique().size-1)
            data_embarque = data_embarque[(data_embarque['Finca'] == finca_seleccionada_rdp) & (data_embarque['Año'] == anio_seleccionado_rdp)]
            st.write("Datos de embarque")
            fig = px.bar(data_embarque, x='Semana', y='Ratio', title='Ratio de Producción', color='Ratio', color_continuous_scale=px.colors.sequential.Turbo,
                         text_auto=True)
            fig.update_traces(texttemplate='%{y:.2f}', textposition='inside', hovertemplate='Semana: %{x}<br>Ratio: %{y:.2f}<br><extra></extra>')
            fig.update_xaxes(range=[0.5, data_embarque['Semana'].max() + 1], dtick=1)
            fig.update_yaxes(range=[0, data_embarque['Ratio'].max() + 2])
            fig.update_layout(xaxis_title='Semana', yaxis_title='Ratio')
            # Agregamos una linea horizontal para un ratio de 4, debe tener un texto que diga "Ratio maximo"
            fig.add_hline(y=2, line_dash="dash", line_color="red", annotation_text="Ratio meta", annotation_position="top right", col="all")
            # Agregamos un texto que diga el significado del ratio en la parte superior derecha
            fig.add_annotation(x=data_embarque['Semana'].max(), y=data_embarque['Ratio'].max()+2, text="Ratio = Total Racimos / Cajas", showarrow=False, xshift=10, yshift=10)
            fig.add_annotation(x=data_embarque['Semana'].max(), y=data_embarque['Ratio'].max()+1, text="Entre mas bajo, mejor", showarrow=False, xshift=10, yshift=10)
            st.plotly_chart(fig, use_container_width=True)

        with ratio_de_produccion_inverso.container():
            data_embarque = procesamiento_datos_embarque_ratio_inverso()
            st.subheader("Filtros para las graficas")
            finca, anio = st.columns(2)
            with finca:
                finca_seleccionada_rdp = st.radio("Seleccionar finca", fincas.keys(), key='17142060469')
            with anio:
                anio_seleccionado_rdp = st.radio("Filtrar por año", data_embarque['Año'].unique(), key='171406204512', index=data_embarque['Año'].unique().size-1)
            data_embarque = data_embarque[(data_embarque['Finca'] == finca_seleccionada_rdp) & (data_embarque['Año'] == anio_seleccionado_rdp)]
            st.write("Datos de embarque")
            fig = px.bar(data_embarque, x='Semana', y='Ratio', title='Ratio de Producción Inverso', color='Ratio', color_continuous_scale=px.colors.sequential.Turbo_r,
                         text_auto=True)
            fig.update_traces(texttemplate='%{y:.2f}', textposition='inside', hovertemplate='Semana: %{x}<br>Ratio: %{y:.2f}<br><extra></extra>')
            fig.update_xaxes(range=[0.5, data_embarque['Semana'].max() + 0.5], dtick=1)
            fig.update_yaxes(range=[0,1])
            fig.update_layout(xaxis_title='Semana', yaxis_title='Ratio')
            # Agregamos una linea horizontal para un ratio de 4, debe tener un texto que diga "Ratio maximo"
            fig.add_hline(y=0.45, line_dash="dash", line_color="red", annotation_text="Ratio Minimo", annotation_position="top right", col="all")
            # Agregamos un texto que diga el significado del ratio en la parte superior derecha
            fig.add_annotation(x=data_embarque['Semana'].max(), y=1, text="Ratio = Cajas / Total Racimos", showarrow=False, xshift=1, yshift=1)
            fig.add_annotation(x=data_embarque['Semana'].max(), y=0.95, text="Entre mas alto, mejor", showarrow=False, xshift=1, yshift=1)
            st.plotly_chart(fig, use_container_width=True)

        with bacota_lote_por_hectarea.container():
            data = procesamiento_datos_sioma_embolse()
            st.subheader("Filtros para las graficas")
            finca_bacota = data['Finca'].unique()
            year_bacota = data['Año'].unique()
            finca, anio, semana = st.columns(3)
            total_hectareas_lote = pd.read_csv('data/lotes.csv')
            with anio:
                anio_seleccionado_bxhxl = st.radio("Filtrar por año", year_bacota, index=year_bacota.size-1, key='1636922135935')
                temp = data[data['Año'] == anio_seleccionado_bxhxl]
            with finca:
                finca_seleccionada_bxhxl = st.radio("Seleccionar finca", finca_bacota, key='2558592342352856')
            temp = temp[temp['Finca'] == finca_seleccionada_bxhxl]
            with semana:
                semana_seleccionada_bxhxl = st.selectbox("Seleccionar semana", np.sort(temp['Semana'].unique()), index=np.sort(temp['Semana'].unique()).size-1)
            temp = temp[temp['Semana'] == semana_seleccionada_bxhxl]
            temp = temp.groupby(by='Semana')['Lote'].value_counts().unstack().fillna(0)
            temp = temp.reset_index()
            temp = temp.melt(id_vars='Semana', var_name='Lote', value_name='Cantidad')
            temp = temp[temp['Cantidad'] != 0]
            for index, row in temp.iterrows():
                for index2, row2 in total_hectareas_lote.iterrows():
                    if row['Lote'] == row2['Lote  Generico']:
                        temp.at[index, 'Bacotas por Hectarea'] = row['Cantidad'] / row2['Tamaño Area Neta']
            try:
                fig = px.bar(temp, x="Lote", y='Bacotas por Hectarea',
                          title='Bacotas por Hectarea', color='Bacotas por Hectarea',
                          color_continuous_scale=px.colors.sequential.Bluered_r,
                          labels={'x': 'Semana', 'y': 'Bacotas por hectarea'},
                          text_auto=True)
                fig.update_traces(texttemplate='%{y:.2f}', textposition='inside', hovertemplate='Lote: %{x}<br>Bacotas por Hectarea: %{y}<br><extra></extra>')
                fig.update_yaxes(range=[0, temp['Bacotas por Hectarea'].max() + (temp['Bacotas por Hectarea'].max()/6)])
                st.plotly_chart(fig, use_container_width=True)
            except ValueError:
                st.warning("No hay datos en la semana seleccionada", icon='⚠️')

        with bacota_lote.container():
            data = procesamiento_datos_sioma_embolse()
            st.subheader("Filtros para las graficas")
            finca_bacota = data['Finca'].unique()
            year_bacota = data['Año'].unique()
            finca, anio, semana = st.columns(3)
            with anio:
                anio_seleccionado_bxl = st.radio("Filtrar por año", year_bacota, index=year_bacota.size-1, key='16369221356935')
            # Filtrar por año
            temp = data[data['Año'] == anio_seleccionado_bxl]
            with finca:
                finca_seleccionada_bxl = st.radio("Seleccionar finca", finca_bacota, key='25585692342352856')
            temp = temp[temp['Finca'] == finca_seleccionada_bxl]
            with semana:
                semana_seleccionada_bxl = st.selectbox("Seleccionar semana", np.sort(temp['Semana'].unique()), key='56114', index=np.sort(temp['Semana'].unique()).size-1)
            temp = temp[temp['Semana'] == semana_seleccionada_bxl]
            temp = temp.groupby(by='Semana')['Lote'].value_counts().unstack().fillna(0)
            temp = temp.reset_index()
            temp = temp.melt(id_vars='Semana', var_name='Lote', value_name='Cantidad')
            temp = temp[temp['Cantidad'] != 0]
            if temp.empty:
                st.warning("No hay datos en la semana seleccionada", icon='⚠️')
            else:
                fig = px.bar(temp, x="Lote", y='Cantidad',
                              title='Cantidad de Bacotas por Lote', color='Cantidad',
                              color_continuous_scale=px.colors.sequential.Bluered_r,
                              labels={'x': 'Semana', 'y': 'Cantidad de Bacotas'},
                              text_auto=True
                              )
                fig.update_xaxes(dtick=1)
                fig.update_yaxes(range=[0, temp['Cantidad'].max() + (temp['Cantidad'].max()/3)], dtick=20)
                st.plotly_chart(fig, use_container_width=True)
        
        with bacota_finca.container():
            data = procesamiento_datos_sioma_embolse()
            st.subheader("Filtros para las graficas")
            finca_bacota = data['Finca'].unique()
            year_bacota = data['Año'].unique()
            finca, anio = st.columns(2)
            with anio:
                anio_seleccionado_bf = st.radio("Filtrar por año", year_bacota, index=year_bacota.size-1, key='163692135935')
                temp = data[data['Año'] == anio_seleccionado_bf]
            with finca:
                finca_seleccionada_bf = st.radio("Seleccionar finca", finca_bacota, key='258592342352856')
                temp = temp[temp['Finca'] == finca_seleccionada_bf]
            temp = temp.groupby(by='Semana')['Finca'].value_counts().unstack().fillna(0)
            temp = temp.reset_index()
            temp = temp.melt(id_vars='Semana', var_name='Finca', value_name='Cantidad')
            temp = temp[temp['Cantidad'] != 0]
            fig = px.bar(temp, x="Semana", y='Cantidad',
                            title='Cantidad de Bacotas por Finca', color='Cantidad',
                            color_continuous_scale=px.colors.sequential.Bluered_r,
                            labels={'x': 'Semana', 'y': 'Cantidad de Bacotas'},
                            text_auto=True
                            )
            fig.update_xaxes(dtick=1)
            fig.update_yaxes(range=[0, temp['Cantidad'].max() + (temp['Cantidad'].max()/6)])
            st.plotly_chart(fig, use_container_width=True)

        with cajas_finca.container():
            data = procesamiento_datos_embarque_cajas()
            st.subheader("Filtros para las graficas")
            finca_caja = data['Finca'].unique()
            year_caja = data['Año'].unique()
            finca, anio = st.columns(2)
            with finca:
                finca_seleccionada_cajas = st.radio("Seleccionar finca", finca_caja, key='9856445')
            with anio:
                anio_seleccionado_cajas = st.radio("Filtrar por año", year_caja, index=year_caja.size-1, key='98484')
            # Filtrar por año
            data = data[data['Año'] == anio_seleccionado_cajas]
            # Filtrar por finca
            data = data[data['Finca'] == finca_seleccionada_cajas]
            fig = px.bar(data, x=data["Semana"], y=data['Cajas'],
                          title='Cajas por Finca', color='Cajas',
                          color_continuous_scale=px.colors.sequential.Bluered_r,
                          labels={'x': 'Semana', 'y': 'Cajas'},
                          text_auto=True)
            fig.update_traces(texttemplate='%{y}', textposition='inside', hovertemplate='Semana: %{x}<br>Cajas: %{y}<br><extra></extra>')
            fig.update_xaxes(dtick=1)
            fig.update_yaxes(range=[0, data['Cajas'].max() + (data['Cajas'].max()/7)])
            st.plotly_chart(fig, use_container_width=True)

    elif pagina == 'Graficos Semanales':
        embolse, desflore, amarre, deshoje, embolse_finca, coco, inventario = st.tabs(["Embolse", "Desflore", "Amarre", "Deshoje", "Embolse por finca", "Coco", "Inventario de Racimos"])
        with embolse:
            st.subheader("Filtros para las graficas")
            data_embolse = procesamiento_datos_sioma_embolse()
            finca, lote, anio = st.columns(3)
            with finca:
                finca_seleccionada_embolse = st.selectbox("Seleccionar finca", data_embolse['Finca'].unique())
            with lote:
                lote_seleccionado_embolse = st.selectbox("Seleccionar lote", data_embolse[(data_embolse['Finca'] == finca_seleccionada_embolse)]['Lote'].sort_values().unique())
            with anio:
                anio_seleccionado_embolse = st.radio("Filtrar por año", data_embolse['Año'].unique(), index=data_embolse['Año'].unique().size-1)
            data_embolse = data_embolse[(data_embolse['Finca'] == finca_seleccionada_embolse) & (data_embolse['Lote'] == lote_seleccionado_embolse) & (data_embolse['Año'] == anio_seleccionado_embolse)]
            temp = data_embolse.groupby(by='Semana')['Color'].value_counts().unstack().fillna(0)
            temp = temp.reset_index()
            temp = temp.melt(id_vars='Semana', var_name='Color', value_name='Cantidad')
            temp = temp[temp['Cantidad'] != 0]
            fig = go.Figure(data=[go.Bar(
                x=temp['Semana'],
                y=temp['Cantidad'],
                marker=dict(color=data_embolse[['Codigo Color', 'Color']].drop_duplicates().set_index('Color').loc[temp['Color']]['Codigo Color'].values),
                hovertemplate='Semana: %{x}<br>Cantidad: %{y}<br><extra></extra>',
                texttemplate='%{y}', textposition='inside'
                )],
            )
            fig.update_xaxes(dtick=1)
            fig.update_layout(title='Embolse', xaxis_title='Semana', yaxis_title='Cantidad')
            st.plotly_chart(fig, use_container_width=True)

        with desflore:
            data_desflore = procesamiento_datos_sioma_desflore()
            st.subheader("Filtros para las graficas")
            finca, lote, anio = st.columns(3)
            with finca:
                finca_seleccionada_desflore = st.radio("Seleccionar finca", data_desflore['Finca'].unique(), key='1714060469')
                data_desflore = data_desflore[data_desflore['Finca'] == finca_seleccionada_desflore]
            with lote:
                lote_seleccionado_desflore = st.selectbox("Seleccionar lote", data_desflore['Lote'].sort_values().unique(), key='1714060486')
            with anio:
                anio_seleccionado_desflore = st.radio("Filtrar por año", data_desflore['Año'].unique(), key='1714060512')
                data_desflore = data_desflore[data_desflore['Año'] == anio_seleccionado_desflore]
            data_desflore = data_desflore[data_desflore['Lote'] == lote_seleccionado_desflore]
            temp = data_desflore.groupby(by='Semana')['Color'].value_counts().unstack().fillna(0)
            temp = temp.reset_index()
            temp = temp.melt(id_vars='Semana', var_name='Color', value_name='Cantidad')
            temp = temp[temp['Cantidad'] != 0]
            fig = go.Figure(data=[go.Bar(
                x=temp['Semana'],
                y=temp['Cantidad'],
                marker=dict(color=data_desflore[['Codigo Color', 'Color']].drop_duplicates().set_index('Color').loc[temp['Color']]['Codigo Color'].values),
                hovertemplate='Semana: %{x}<br>Cantidad: %{y}<br>Color: %{marker.color}<extra></extra>',
                text=[f"{color} - {cantidad}" for color, cantidad in zip(temp['Color'], temp['Cantidad'])],
                )]
            )
            fig.update_xaxes(dtick=1)
            st.plotly_chart(fig, use_container_width=True)

        with amarre:
            st.write("Amarre")
            st.subheader("Por implementar")

        with deshoje:
            st.write("Deshoje")
            st.subheader("Por implementar")

        with embolse_finca:
            data_embolse = procesamiento_datos_sioma_embolse()
            st.subheader("Filtros para las graficas")
            finca, anio = st.columns(2)
            with finca:
                finca_seleccionada_embolse = st.radio("Seleccionar finca", data_embolse['Finca'].unique(), key='17140460469')
            with anio:
                anio_seleccionado_embolse = st.radio("Filtrar por año", data_embolse['Año'].unique(), key='17140620512', index=data_embolse['Año'].unique().size-1)
            data_embolse = data_embolse[(data_embolse['Finca'] == finca_seleccionada_embolse) & (data_embolse['Año'] == anio_seleccionado_embolse)]
            temp = data_embolse.groupby(by='Semana')['Color'].value_counts().unstack().fillna(0)
            temp = temp.reset_index()
            temp = temp.melt(id_vars='Semana', var_name='Color', value_name='Cantidad')
            temp = temp[temp['Cantidad'] != 0]
            fig = go.Figure(data=[go.Bar(
                x=temp['Semana'],
                y=temp['Cantidad'],
                marker=dict(color=data_embolse[['Codigo Color', 'Color']].drop_duplicates().set_index('Color').loc[temp['Color']]['Codigo Color'].values),
                hovertemplate='Semana: %{x}<br>Cantidad: %{y}<br><extra></extra>',
                texttemplate='%{y}', textposition='inside'
                )]
            )
            fig.update_xaxes(dtick=1)
            st.plotly_chart(fig, use_container_width=True)

        with coco:
            data_coco = procesamiento_datos_sioma_coco()
            data_coco = data_coco[data_coco['Tipo de labor'] == 'Control fitosanitario']
            finca_seleccionada_coco = st.radio("Seleccionar finca", data_coco['Finca'].unique(), key='664715')
            data_coco = data_coco[data_coco['Finca'] == finca_seleccionada_coco]
            mapa, pie = st.columns(2)
            fig = px.scatter_mapbox(data_coco, lat='lat', lon='lng', zoom=16, mapbox_style='carto-darkmatter', color_discrete_sequence=['lime'], hover_name='Finca', hover_data=['Fecha', 'Semana'], title='Control fitosanitario', labels={'lat': 'Latitud', 'lng': 'Longitud'})
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            fig.update_layout(mapbox_bounds={'north': 8.9203, 'south': 8.8, 'east': -76.1325, 'west': -76.7793})
            mapa.plotly_chart(fig, use_container_width=True)
            temp = data_coco.groupby(by='Semana')['Finca'].value_counts().unstack().fillna(0)
            temp = temp.reset_index()
            temp = temp.melt(id_vars='Semana', var_name='Finca', value_name='Cantidad')
            temp = temp[temp['Cantidad'] != 0]
            pie.plotly_chart(px.pie(temp, values='Cantidad', names='Finca', title='Control fitosanitario por finca', color='Cantidad'), use_container_width=True)

        with inventario:
            data_embolse_inventario = procesamiento_datos_sioma_embolse()
            data_corte_inventario = procesamiento_datos_sioma_corte()
            data_repique_inventario = procesamiento_datos_sioma_repique()
            st.subheader("Filtros para las graficas")
            anio = data_embolse_inventario['Año'].unique().max()
            # Fecha por semana
            data_embolse_inventario = data_embolse_inventario[data_embolse_inventario['Año'] == anio]
            data_corte_inventario = data_corte_inventario[data_corte_inventario['Año'] == anio]
            data_repique_inventario = data_repique_inventario[data_repique_inventario['Año'] == anio]
            semana_inventario = st.selectbox("Seleccionar semana", np.sort(data_embolse_inventario['Semana'].unique()), key='5615')
            temp_embolse = data_embolse_inventario.groupby(by='Semana')['Color'].value_counts().unstack().fillna(0)
            temp_embolse = temp_embolse.reset_index()
            temp_embolse = temp_embolse.melt(id_vars='Semana', var_name='Color', value_name='Cantidad')
            temp_embolse = temp_embolse[temp_embolse['Cantidad'] != 0]
            temp = temp_embolse.groupby(by='Semana').sum(numeric_only=True)
            temp = temp.reset_index()
            
            st.dataframe(temp)
            
            temp_embolse.reset_index(drop=True, inplace=True)
            temp_corte = data_corte_inventario.groupby(by='Semana')['Color'].value_counts().unstack().fillna(0)
            temp_corte = temp_corte.reset_index()
            temp_corte = temp_corte.melt(id_vars='Semana', var_name='Color', value_name='Cantidad')
            temp_corte = temp_corte[temp_corte['Cantidad'] != 0]
            temp_corte.reset_index(drop=True, inplace=True)
            temp_repique = data_repique_inventario.groupby(by='Semana')['Color'].value_counts().unstack().fillna(0)
            temp_repique = temp_repique.reset_index()
            temp_repique = temp_repique.melt(id_vars='Semana', var_name='Color', value_name='Cantidad')
            temp_repique = temp_repique[temp_repique['Cantidad'] != 0]
            temp_repique.reset_index(drop=True, inplace=True)
            st.dataframe(temp_embolse)
            # El inventario se calcula los racimos de embolse - los racimos de corte - los racimos de repique
            temp_inventario = temp_embolse.copy()
            temp_inventario = temp_inventario[temp_inventario['Cantidad'] != 0]
            temp_inventario.reset_index(drop=True, inplace=True)
            fig = go.Figure(data=[go.Bar(
                x=temp_inventario['Semana'],
                y=temp_inventario['Cantidad'],
                marker=dict(color=data_embolse_inventario[['Codigo Color', 'Color']].drop_duplicates().set_index('Color').loc[temp_inventario['Color']]['Codigo Color'].values),
                hovertemplate='Semana: %{x}<br>Racimos disponibles: %{y}<br><extra></extra>',
                texttemplate='%{y}', textposition='inside'
                ),
                go.Bar(
                    x=temp['Semana'],
                    y=temp['Cantidad'],
                    marker=dict(color='black'),
                    hovertemplate='Semana: %{x}<br>Racimos totales: %{y}<br><extra></extra>',
                    texttemplate='%{y}', textposition='inside'
                )
            ])
            fig.update_xaxes(dtick=1)
            fig.update_layout(title='Inventario de Racimos', xaxis_title='Semana', yaxis_title='Cantidad')
            st.plotly_chart(fig, use_container_width=True)
            
    elif pagina == 'Tareas Periodicas':
        st.write("Tareas Periodicas")
        control_maleza, desmache, resiembra, fertilizacion, control_sigatoka, abono, abono_foliar = st.tabs([
                "Control de maleza",
                "Desmache",
                "Resiembra", 
                "Fertilizacion",
                "Control de sigatoka",
                "Abono",
                "Abono foliar"
                ])
        with control_maleza:
            st.write("Filtros para las graficas")
            data = procesamiento_datos_rdt()
            #labores = data['Labores'].unique().tolist()
            # Mostrar solo las labores que contengan la palabra 'maleza'
            labores = 'Fumigacion  Control Maleza '
            #labores = [labor for labor in labores if 'maleza' in labor.lower()]
            #test = st.multiselect("Seleccionar limpieza labor", labores, key='17141396121')
            # usar los valores de test para filtrar el dataframe
            data = data[data['Labores'] == labores].reset_index(drop=True)
            columna_finca, columna_lote, columna_anio = st.columns(3)
            with columna_anio:
                anio = st.radio("Filtrar por año", data['Año'].unique(), key='1714139611', index=data['Año'].unique().size-1)
            data = data[data['Año'] == anio]
            with columna_finca:
                finca_seleccionada_maleza = st.selectbox("Seleccionar finca", fincas.keys(), key='1714139612')
            with columna_lote:
                lotes_maleza = st.selectbox("Seleccionar el lote", fincas.get(finca_seleccionada_maleza),key='1714153623')
            data = data[data['Codigo Generico L1'] == lotes_maleza].reset_index(drop=True)
            # Agrupar por Semana, Codigo Generico L1 y Labores, hacer la sumatoria de 'Unidades Primer Lote'
            temp = data.groupby(['Año', 'Semana', 'Codigo Generico L1', 'Labores']).sum(numeric_only=True).reset_index()
            for index, row in temp.iterrows():
                for index2, row2 in lotes_finca.iterrows():
                    if row['Codigo Generico L1'] == row2['Lote  Generico']:
                        temp.at[index, 'Porcentaje'] = (row['Unidades Primer Lote'] / row2['Tamaño Area Neta']) * 100
            temp.reset_index(drop=True, inplace=True)
            try:
                fig = px.bar(temp, x='Semana', y='Porcentaje', title='Control de maleza',
                              hover_data=['Semana', 'Porcentaje'], range_y=[0, 100], color='Porcentaje',color_continuous_scale=px.colors.sequential.Bluered_r, text='Porcentaje')
                fig.update_xaxes(tickmode='linear')
                fig.update_traces(hovertemplate='Semana: %{x}<br>%{y}%<br><extra></extra>', texttemplate='%{y:.2f}%', textposition='inside')
                fig.update_layout(xaxis_title='Semana', yaxis_title='Porcentaje')
                st.plotly_chart(fig, use_container_width=True)
            except ValueError:
                st.warning("No hay datos en el lote seleccionado", icon='⚠️')

        with desmache:
            st.write("Filtro para las graficas")
            data_desmache = procesamiento_datos_rdt()
            labores = 'Desmache'
            data_desmache = data_desmache[data_desmache['Labores'] == labores].reset_index(drop=True)
            columna_finca, columna_lote, columna_anio = st.columns(3)
            with columna_anio:
                anio = st.radio("Filtrar por año", data_desmache['Año'].unique(), key='1714139618', index=data_desmache['Año'].unique().size-1)
            data_desmache = data_desmache[data_desmache['Año'] == anio]
            with columna_finca:
                finca_seleccionada_desmache = st.selectbox("Seleccionar finca", fincas.keys(), key='1714139617')
            with columna_lote:
                lotes_desmache = st.selectbox("Seleccionar el lote", fincas.get(finca_seleccionada_desmache),key='1714153626')
            data_desmache = data_desmache[data_desmache['Codigo Generico L1'] == lotes_desmache].reset_index(drop=True)
            # Agrupar por Semana, Codigo Generico L1 y Labores, hacer la sumatoria de 'Unidades Primer Lote'
            temp = data_desmache.groupby(['Año', 'Semana', 'Codigo Generico L1', 'Labores']).sum(numeric_only=True).reset_index()
            for index, row in temp.iterrows():
                for index2, row2 in lotes_finca.iterrows():
                    if row['Codigo Generico L1'] == row2['Lote  Generico']:
                        temp.at[index, 'Porcentaje'] = (row['Unidades Primer Lote'] / row2['Tamaño Area Neta']) * 100
            temp.reset_index(drop=True, inplace=True)
            try:
                fig = px.bar(temp, x='Semana', y='Porcentaje', title='Desmache', hover_data=['Semana', 'Porcentaje'], range_y=[0, 100], color='Porcentaje',color_continuous_scale=px.colors.sequential.Bluered_r)
                fig.update_xaxes(dtick=1)
                fig.update_traces(hovertemplate='Semana: %{x}<br>%{y}%<br><extra></extra>', texttemplate='%{y:.2f}%', textposition='inside')
                fig.update_layout(xaxis_title='Semana', yaxis_title='Porcentaje')
                st.plotly_chart(fig, use_container_width=True)
            except ValueError:
                st.warning("No hay datos en el lote seleccionado", icon='⚠️')

        with resiembra:
            st.write("Filtros para las graficas")
            data_resiembra = procesamiento_datos_sioma_resiembra()
            finca, lote, anio = st.columns(3)
            with finca:
                finca_seleccionada_resiembra = st.selectbox("Seleccionar finca", data_resiembra['Finca'].unique(), key='17141394611')
            with lote:
                lote_seleccionado_resiembra = st.selectbox("Seleccionar lote", data_resiembra[(data_resiembra['Finca'] == finca_seleccionada_resiembra)]['Lote'].sort_values().unique(), key='17174153623')
            with anio:
                anio_seleccionado_resiembra = st.radio("Filtrar por año", data_resiembra['Año'].unique(), key='1714153362301')
            data_resiembra = data_resiembra[(data_resiembra['Finca'] == finca_seleccionada_resiembra) & (data_resiembra['Lote'] == lote_seleccionado_resiembra) & (data_resiembra['Año'] == anio_seleccionado_resiembra)]
            temp = data_resiembra.groupby(by='Semana')['Lote'].value_counts().unstack().fillna(0)
            temp = temp.reset_index()
            temp = temp.melt(id_vars='Semana', var_name='Lote', value_name='Cantidad')
            temp = temp[temp['Cantidad'] != 0]
            if temp.empty:
                st.warning("No hay datos en el lote seleccionado", icon='⚠️')
            else:
                try:
                    fig = px.bar(temp, x='Semana', y='Cantidad', title='Resiembra', hover_data=['Semana', 'Cantidad'], color='Cantidad',color_continuous_scale=px.colors.sequential.Bluered_r)
                    fig.update_traces(hovertemplate='Semana: %{x}<br>Cantidad: %{y}<br><extra></extra>', texttemplate='%{y}', textposition='inside')
                    fig.update_xaxes(dtick=1)
                    # rango de y
                    fig.update_yaxes(range=[0, temp['Cantidad'].max() + 10])
                    fig.update_layout(xaxis_title='Semana', yaxis_title='Unidades')
                    # Colocar la figura en el medio
                    st.plotly_chart(fig, use_container_width=True)
                except ValueError:
                    st.warning("No hay datos en el lote seleccionado", icon='⚠️')

        with fertilizacion:
            st.write("Fertilizacion")
            st.subheader("Por implementar")

        with control_sigatoka:
            st.write("Filros para las graficas")
            data = procesamiento_datos_rdt()
            labores = 'Control'
            nombre_labor = ['Control foliar', 'Control foliar con Nitrato de potasio y menores']
            data = data[data['Nombre Labor'].isin(nombre_labor)].reset_index(drop=True)
            columna_finca, columna_lote, columna_anio = st.columns(3)
            with columna_anio:
                anio = st.radio("Filtrar por año", data['Año'].unique(), key='17141396121')
            data = data[data['Año'] == anio]
            with columna_finca:
                finca_seleccionada_sigatoka = st.selectbox("Seleccionar finca", fincas.keys(), key='171413961214')
            with columna_lote:
                lotes_sigatoka = st.selectbox("Seleccionar el lote", fincas.get(finca_seleccionada_sigatoka),key='171415362301')
            data = data[data['Codigo Generico L1'] == lotes_sigatoka].reset_index(drop=True)
            #Agrupar por Semana, Codigo Generico L1 y Labores, hacer la sumatoria de 'Unidades Primer Lote'
            #Debido a que esta labor se puede realizar en distintos lotes al mismo tiempo puede que tengamos valores iguales en 'Codigo Generico L1' y 'Codigo Generico L2'
            #Por lo tanto, se debe sumar las unidades de los lotes iguales
            #Pero puede que tambien se realice en la misma semana la misma labor pero con diferente nombre, por lo tanto, se debe sumar las unidades de las labores iguales 
            temp1 = data.groupby(['Año', 'Semana', 'Codigo Generico L1', 'Labores']).sum(numeric_only=True).reset_index()
            temp = pd.melt(temp1, id_vars=['Año', 'Semana', 'Codigo Generico L1', 'Labores'], value_vars=['Unidades Primer Lote'], var_name='Unidades')
            for index, row in temp.iterrows():
                for index2, row2 in lotes_finca.iterrows():
                    if row['Codigo Generico L1'] == row2['Lote  Generico']:
                        temp.at[index, 'Porcentaje'] = (row['value'] / row2['Tamaño Area Neta']) * 100
            temp = temp.groupby(['Año', 'Semana', 'Labores']).sum(numeric_only=True).reset_index()
            temp.reset_index(drop=True, inplace=True)
            try:
                fig = px.bar(temp, x='Semana', y='Porcentaje', title='Control de sigatoka', hover_data=['Semana', 'Porcentaje'], range_y=[0, 100], color='Porcentaje',color_continuous_scale=px.colors.sequential.Bluered_r)
                fig.update_xaxes(dtick=1)
                fig.update_traces(hovertemplate='Semana: %{x}<br>%{y}%<br><extra></extra>', texttemplate='%{y:.2f}%', textposition='inside')
                fig.update_layout(xaxis_title='Semana', yaxis_title='Porcentaje')
                st.plotly_chart(fig, use_container_width=False)
            except ValueError:
                st.warning("No hay datos en el lote seleccionado", icon='⚠️')

        with abono:
            st.write("Abono")
            st.subheader("Por implementar")

        with abono_foliar:
            st.write("Abono foliar")
            st.subheader("Por implementar")


if __name__ == '__main__':
    run()