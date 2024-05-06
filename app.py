import dropbox.exceptions
import streamlit as st
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
    flow = dropbox.DropboxOAuth2FlowNoRedirect(KEY, SECRET, token_access_type="legacy")
    authorize_url = flow.start()
    st.write("Ir a la siguiente URL para autorizar la aplicación:")
    st.link_button("Ir a la página de autorización", authorize_url)
    auth_code = st.text_input("Ingrese el código de autorización aquí: ").strip()
    try:
        oauth_result = flow.finish(auth_code)
    except Exception as e:
        print("Error: %s" % (e,))
        return
    st.code(str(oauth_result.access_token), language="textfile")
    return oauth_result.access_token

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
    excel = r'data/Dropbox/LIQUIDADOR DE EMBARQUE.xlsx'
    sheet = 'CALCULO PAGO'
    df = pd.read_excel(excel, sheet_name=sheet)
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

@st.cache_data(ttl='12h')
def procesamiento_datos_rdt():
    df = pd.read_excel(r'data/Dropbox/RDT  26  de Abril de 2024  (1) (version 1).xlsb.xlsx', sheet_name='RDT')
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
            dropbox_oauth()
            with st.spinner("Descargando archivos de Dropbox"):
                dbx = dropbox.Dropbox(TOKEN)
                # Buscar el archivo de RDT 
                search_excel_rdt(dbx, folder_data_dropbox, '/TROPICAL  2022/Nomina Dopbox/RDT 2023')
                st.success("RDT descargado")
                # Buscar el archivo de EMBARQUE
                search_excel_embarque(dbx, folder_data_dropbox, '/TROPICAL  2022/Embarque Dropbox')
                st.success("Embarque descargado")
                st.success("Archivos descargados con exito")

    elif pagina == 'Graficos de Produccion':
        caja_por_hectarea, bacota_por_hectarea, ratio_de_produccion, bacota_lote_por_hectarea = st.tabs(
            ["Caja por hectarea",
             "Bacota por hectarea",
             "Ratio de Producción",
             "Bacota por lote por hectarea"
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
                          title='Cajas', color='Cajas por Hectarea',
                          color_continuous_scale=px.colors.sequential.Jet,
                          labels={'x': 'Semana', 'y': 'Cajas por hectarea'})
            fig.update_yaxes(range=[0, data['Cajas por Hectarea'].max() + (data['Cajas por Hectarea'].max()/7)])
            print(data['Cajas por Hectarea'].max())
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
                          color_continuous_scale=px.colors.sequential.Jet,
                          labels={'x': 'Semana', 'y': 'Bacotas por hectarea'})
            fig.update_yaxes(range=[0, temp['Bacotas por Hectarea'].max() + (temp['Bacotas por Hectarea'].max()/7)])
            st.plotly_chart(fig, use_container_width=True)
        
        with ratio_de_produccion.container():
            st.write("Ratio de Producción (por implementar)")

        with bacota_lote_por_hectarea.container():
            data = procesamiento_datos_sioma_embolse()
            st.subheader("Filtros para las graficas")
            finca_bacota = data['Finca'].unique()
            year_bacota = data['Año'].unique()
            finca, anio, semana = st.columns(3)
            total_hectareas_lote = pd.read_csv('data/lotes.csv')
            with finca:
                finca_seleccionada_bxhxl = st.radio("Seleccionar finca", finca_bacota, key='255856952856')
            with anio:
                anio_seleccionado_bxhxl = st.radio("Filtrar por año", year_bacota, index=year_bacota.size-1, key='16369256935')
            # Filtrar por año
            temp = data[data['Año'] == anio_seleccionado_bxhxl]
            with semana:
                semana_seleccionada_bxhxl = st.slider(
                    "Seleccionar semana",
                    temp['Semana'].unique().min(),
                    temp['Semana'].unique().max(),
                    temp['Semana'].unique().min(),
                    1
                    )
            temp = temp[temp['Semana'] == semana_seleccionada_bxhxl]
            temp = temp[temp['Finca'] == finca_seleccionada_bxhxl]
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
                          color_continuous_scale=px.colors.sequential.Jet,
                          labels={'x': 'Semana', 'y': 'Bacotas por hectarea'})
                fig.update_yaxes(range=[0, temp['Bacotas por Hectarea'].max() + (temp['Bacotas por Hectarea'].max()/6)])
                st.plotly_chart(fig, use_container_width=True)
            except ValueError:
                st.warning("No hay datos en el lote seleccionado", icon='⚠️')

    elif pagina == 'Graficos Semanales':
        embolse, desflore, amarre, deshoje = st.tabs(["Embolse", "Desflore", "Amarre", "Deshoje"])
        with embolse:
            st.subheader("Filtros para las graficas")
            data_embolse = procesamiento_datos_sioma_embolse()
            finca, lote, anio = st.columns(3)
            with finca:
                finca_seleccionada_embolse = st.selectbox("Seleccionar finca", data_embolse['Finca'].unique())
            with lote:
                lote_seleccionado_embolse = st.selectbox("Seleccionar lote", data_embolse[(data_embolse['Finca'] == finca_seleccionada_embolse)]['Lote'].sort_values().unique())
            with anio:
                anio_seleccionado_embolse = st.radio("Filtrar por año", data_embolse['Año'].unique())
            data_embolse = data_embolse[(data_embolse['Finca'] == finca_seleccionada_embolse) & (data_embolse['Lote'] == lote_seleccionado_embolse) & (data_embolse['Año'] == anio_seleccionado_embolse)]
            temp = data_embolse.groupby(by='Semana')['Color'].value_counts().unstack().fillna(0)
            temp = temp.reset_index()
            temp = temp.melt(id_vars='Semana', var_name='Color', value_name='Cantidad')
            temp = temp[temp['Cantidad'] != 0]
            fig = go.Figure(data=[go.Bar(
                x=temp['Semana'],
                y=temp['Cantidad'],
                marker=dict(color=data_embolse[['Codigo Color', 'Color']].drop_duplicates().set_index('Color').loc[temp['Color']]['Codigo Color'].values),
                hovertemplate='Semana: %{x}<br>Cantidad: %{y}<br>Color: %{marker.color}<extra></extra>'
                )],
            )
            fig.update_layout(title='Embolse', xaxis_title='Semana', yaxis_title='Cantidad')
            st.plotly_chart(fig, use_container_width=True)

        with desflore:
            data_desflore = procesamiento_datos_sioma_desflore()
            st.subheader("Filtros para las graficas")
            finca, lote, anio = st.columns(3)
            with finca:
                finca_seleccionada_desflore = st.radio("Seleccionar finca", data_desflore['Finca'].unique(), key='1714060469')
            with lote:
                lote_seleccionado_desflore = st.selectbox("Seleccionar lote", data_desflore[(data_desflore['Finca'] == finca_seleccionada_desflore)]['Lote'].sort_values().unique(), key='1714060486')
            with anio:
                anio_seleccionado_desflore = st.radio("Filtrar por año", data_desflore['Año'].unique(), key='1714060512')
            data_embolse = data_embolse[(data_embolse['Finca'] == finca_seleccionada_desflore) & (data_desflore['Lote'] == lote_seleccionado_desflore) & (data_desflore['Año'] == anio_seleccionado_desflore)]
            temp = data_desflore.groupby(by='Semana')['Color'].value_counts().unstack().fillna(0)
            temp = temp.reset_index()
            temp = temp.melt(id_vars='Semana', var_name='Color', value_name='Cantidad')
            temp = temp[temp['Cantidad'] != 0]
            fig = go.Figure(data=[go.Bar(
                x=temp['Semana'],
                y=temp['Cantidad'],
                marker=dict(color=data_desflore[['Codigo Color', 'Color']].drop_duplicates().set_index('Color').loc[temp['Color']]['Codigo Color'].values),
                hovertemplate='Semana: %{x}<br>Cantidad: %{y}<br>Color: %{marker.color}<extra></extra>'
                )]
            )
            st.plotly_chart(fig, use_container_width=True)
        with amarre:
            st.write("Amarre")
            st.subheader("Por implementar")
        with deshoje:
            st.write("Deshoje")
            st.subheader("Por implementar")
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
                fig = px.bar(temp, x='Semana', y='Porcentaje', title='Control de maleza', hover_data=['Semana', 'Porcentaje'], range_y=[0, 100], color='Porcentaje',color_continuous_scale=px.colors.sequential.Jet)
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
                fig = px.bar(temp, x='Semana', y='Porcentaje', title='Desmache', hover_data=['Semana', 'Porcentaje'], range_y=[0, 100], color='Porcentaje',color_continuous_scale=px.colors.sequential.Jet)
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
                    fig = px.bar(temp, x='Semana', y='Cantidad', title='Resiembra', hover_data=['Semana', 'Cantidad'], color='Cantidad',color_continuous_scale=px.colors.sequential.Jet)
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
                fig = px.bar(temp, x='Semana', y='Porcentaje', title='Control de sigatoka', hover_data=['Semana', 'Porcentaje'], range_y=[0, 100], color='Porcentaje',color_continuous_scale=px.colors.sequential.Jet)
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