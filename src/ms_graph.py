import streamlit as st
from O365 import Account
import os

def conectar_onedrive():
    # Datos de los Secrets
    client_id = st.secrets["microsoft"]["client_id"]
    client_secret = st.secrets["microsoft"]["client_secret"]
    
    credentials = (client_id, client_secret)
    # Usamos un archivo local para guardar el token y no pedir login cada vez
    token_path = 'data/token.txt'
    
    account = Account(credentials, token_backend=None) # En la nube usaremos otra estrategia, pero para empezar:
    
    if not account.is_authenticated:
        # Esto generará un link en la consola de Streamlit la primera vez
        account.authenticate(scopes=['files.readwrite.all', 'offline_access'])
    
    return account.storage().get_default_drive()

def descargar_db_onedrive():
    drive = conectar_onedrive()
    # Busca el archivo en la carpeta que creamos
    item = drive.get_item_by_path('FactuPro_App/FactuPro_DB.xlsx')
    item.download(to_path='data/temp_db.xlsx')
    return 'data/temp_db.xlsx'

def subir_archivo_onedrive(ruta_local, carpeta_destino, nombre_archivo):
    drive = conectar_onedrive()
    # carpeta_destino ej: "FactuPro_App/Facturas/2024/Mayo"
    try:
        folder = drive.get_item_by_path(carpeta_destino)
    except:
        # Lógica simplificada: asume que la carpeta existe o la crea el usuario
        st.error(f"La carpeta {carpeta_destino} no existe en OneDrive.")
        return
    
    folder.upload(ruta_local, item_name=nombre_archivo)