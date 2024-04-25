import random
import string
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

# Diccionarios con informacion de fincas y lotes
fincas = {
    'San Pedro': ['S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S07', 'S08', 'S09'],
    'Uveros' : ['U06', 'U07'],
    'Damaquiel': ['D08', 'D09', 'D10', 'D11'],
    'Pedrito': ['P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10', 'P11', 'P12', 'P13', 'PN20', 'P15'],
    'Montañita': ['M01', 'M02', 'M03', 'M04', 'M05']
    }

#st.write("# Analisis de datos de Tropical Food Export SAS")
st.title("Analisis de datos de Tropical Food Export SAS")

paginas = ['Inicio', 'Graficos de Produccion', 'Graficos Semanales', 'Tareas Periodicas']

@st.cache_data(ttl='12h')
def procesamiento_datos_embarque():
    excel = r'c:\Users\alext\Dropbox\TROPICAL  2022 oficina\Embarque Dropbox\LIQUIDADOR DE EMBARQUE.xlsx'
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

def procesamiento_datos_sioma_embolse():
    df = pd.read_excel(r'c:\Users\alext\Downloads\embolse.xlsx')
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

def procesamiento_datos_sioma_desflore():
    df = pd.read_excel(r'c:\Users\alext\Downloads\desflore.xlsx')
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
    
def run():
    st.sidebar.title("Menu")
    pagina = st.sidebar.radio("Seleccionar pagina", paginas)

    if pagina == 'Inicio':
        st.markdown('''
                    Bienvenido a la aplicación de análisis de datos de Tropical Food Export SAS.
                    En la parte izquierda se encuentra el menú de opciones, donde se puede seleccionar la opción deseada.
                    Estan disponibles las siguientes opciones:
                    - Gráficos de producción
                    - Graficos semanales (Embolse, Desflore, Amarre, Deshoje)
                    - Graficos de tareas periodicas
                    ''')
    elif pagina == 'Graficos de Produccion':
        caja_por_hectarea, bacota_por_hectarea = st.tabs(["Caja por hectarea", "Bacota por hectarea"])
        #st.write("Caja por Hectarea")
        with caja_por_hectarea.container():
            data = procesamiento_datos_embarque()
            st.subheader("Filtros para las graficas")
            fincas = data['Finca'].unique()
            year = data['Año'].unique()
            finca, anio = st.columns(2)
            with finca:
                finca_seleccionada_cxh = st.radio("Seleccionar finca", fincas)
            with anio:
                anio_seleccionado_cxh = st.radio("Filtrar por año", year, index=year.size-1)
            # Filtrar por año
            data = data[data['Año'] == anio_seleccionado_cxh]
            # Filtrar por finca
            data = data[data['Finca'] == finca_seleccionada_cxh]
            fig = px.bar(data, x=data["Semana"], y=data['Cajas por Hectarea'],
                          title='Cajas', color_discrete_sequence=['#F4D03F'],
                          labels={'x': 'Semana', 'y': 'Cajas por hectarea'})
            st.plotly_chart(fig, use_container_width=True)
            
        with bacota_por_hectarea.container():
            data = procesamiento_datos_sioma_embolse()
            st.subheader("Filtros para las graficas")
            fincas = data['Finca'].unique()
            year = data['Año'].unique()
            finca, anio = st.columns(2)
            total_hectareas = pd.read_csv('data/total_hectareas_por_finca.csv')
            with finca:
                finca_seleccionada_bxh = st.radio("Seleccionar finca", fincas, key='sdasfadg')
            with anio:
                anio_seleccionado_bxh = st.radio("Filtrar por año", year, index=year.size-1, key='asdasd')
            # Sumar la cantidad de bolsas, dependiendo de la finca
            # Filtrar por año
            temp = data[data['Año'] == anio_seleccionado_bxh]
            temp = data.groupby(by='Semana')['Finca'].value_counts().unstack().fillna(0)
            temp = temp.reset_index()
            temp = temp.melt(id_vars='Semana', var_name='Finca', value_name='Cantidad')
            temp = temp[temp['Cantidad'] != 0]
            print(temp)
            for index, row in temp.iterrows():
                for index2, row2 in total_hectareas.iterrows():
                    if row['Finca'] == row2['Finca']:
                        temp.at[index, 'Bacotas por Hectarea'] = row['Cantidad'] / row2['Tamaño Area Neta']
            # Filtrar por finca
            temp = temp[temp['Finca'] == finca_seleccionada_bxh]
            #temp = temp.groupby(by='Semana')['Cantidad'].sum().reset_index()
            fig = px.bar(temp, x="Semana", y='Bacotas por Hectarea',
                          title='Bacotas por Hectarea', color_discrete_sequence=['#F4D03F'],
                          labels={'x': 'Semana', 'y': 'Bacotas por hectarea'})
            st.plotly_chart(fig, use_container_width=True)

    elif pagina == 'Graficos Semanales':
        embolse, desflore, amarre, deshoje = st.tabs(["Embolse", "Desflore", "Amarre", "Deshoje"])
        with embolse:
            data_embolse = procesamiento_datos_sioma_embolse()
            finca, lote, anio = st.columns(3)
            with finca:
                finca_seleccionada_embolse = st.radio("Seleccionar finca", data_embolse['Finca'].unique())
            with lote:
                lote_seleccionado_embolse = st.radio("Seleccionar lote", data_embolse[(data_embolse['Finca'] == finca_seleccionada_embolse)]['Lote'].sort_values().unique())
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
                marker=dict(color=data_embolse[['Codigo Color', 'Color']].drop_duplicates().set_index('Color').loc[temp['Color']]['Codigo Color'].values))],
            )
            st.plotly_chart(fig, use_container_width=True)

        with desflore:
            data_desflore = procesamiento_datos_sioma_desflore()
            finca, lote, anio = st.columns(3)
            with finca:
                finca_seleccionada_desflore = st.radio("Seleccionar finca", data_desflore['Finca'].unique(), key='1714060469')
            with lote:
                lote_seleccionado_desflore = st.radio("Seleccionar lote", data_desflore[(data_desflore['Finca'] == finca_seleccionada_desflore)]['Lote'].sort_values().unique(), key='1714060486')
            with anio:
                anio_seleccionado_desflore = st.radio("Filtrar por año", data_desflore['Año'].unique(), key='1714060512')
            data_embolse = data_embolse[(data_embolse['Finca'] == finca_seleccionada_desflore) & (data_desflore['Lote'] == lote_seleccionado_desflore) & (data_desflore['Año'] == anio_seleccionado_desflore)]
            temp = data_desflore.groupby(by='Semana')['Color'].value_counts().unstack().fillna(0)
            temp = temp.reset_index()
            temp = temp.melt(id_vars='Semana', var_name='Color', value_name='Cantidad')
            temp = temp[temp['Cantidad'] != 0]
            print(procesamiento_datos_sioma_desflore())
            print(temp)
            st.dataframe(temp, hide_index=True)
            fig = go.Figure(data=[go.Bar(
                x=temp['Semana'],
                y=temp['Cantidad'],
                marker=dict(color=data_desflore[['Codigo Color', 'Color']].drop_duplicates().set_index('Color').loc[temp['Color']]['Codigo Color'].values))],
            )
            st.plotly_chart(fig, use_container_width=True)
        with amarre:
            st.write("Amarre")
            st.subheader("Por implementar")
        with deshoje:
            st.write("Deshoje")
            st.subheader("Por implementar")


if __name__ == '__main__':
    run()