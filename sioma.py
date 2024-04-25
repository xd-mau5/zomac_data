import random
import string
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

fincas = {
    'San Pedro': ['S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S07', 'S08', 'S09'],
    'Uveros' : ['U06', 'U07'],
    'Damaquiel': ['D08', 'D09', 'D10', 'D11'],
    'Pedrito': ['P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10', 'P11', 'P12', 'P13', 'PN20', 'P15']
    }

def cargar_datos_embolse():
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
    # codigo_color_dict = dict(zip(color['Color'], color['Codigo Color']))
    df['Codigo Color'] = df['Color'].map(dict(zip(color['Color'], color['Codigo Color'])))
    # df = df.drop(columns=['lat', 'lng', 'Fecha'])
    # df = df.groupby(by='Semana')['Tipo de labor'].value_counts().unstack().fillna(0)
    # df['Total'] = df.sum(axis=1)
    return df


data = cargar_datos_embolse()
colores = pd.read_csv('data/colores_semana_embolse.csv')
temp = cargar_datos_embolse().groupby(by='Semana')['Color'].value_counts().unstack().fillna(0)
temp = temp.reset_index()
temp = temp.melt(id_vars='Semana', var_name='Color', value_name='Cantidad')
temp = temp[temp['Cantidad'] != 0]
print(temp)
st.dataframe(data, use_container_width=True)
#fig = px.bar(data, x='Semana', y='Cantidad', color='Semana')
fig = go.Figure(data=[go.Bar(
    x=temp['Semana'],
    y=temp['Cantidad'],
    marker=dict(color=data[['Codigo Color', 'Color']].drop_duplicates().set_index('Color').loc[temp['Color']]['Codigo Color'].values))],
)
# Sumar la cantidad de cajas por semana
temp2 = temp.groupby(by='Semana')['Cantidad'].sum().reset_index()
print(temp2)
#fig.add_trace(go.Line(x=temp2['Semana'], y=temp2['Cantidad'], mode='lines', name='lines'))
st.dataframe(temp2, hide_index=True)
fig.update_layout(title='Embolse', xaxis_title='Semana', yaxis_title='Cantidad')
st.plotly_chart(fig, use_container_width=True)

fig2 = px.histogram(temp, x='Semana', y='Cantidad', color='Color')
st.plotly_chart(fig2, use_container_width=True)
#file = st.file_uploader(type=['xlsx', 'csv', 'feather'], label='Cargar archivo')
#df_test = pd.read_csv(file)
#st.dataframe(df_test)
#print(df_test)