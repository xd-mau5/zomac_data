import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

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

#def run_UI():