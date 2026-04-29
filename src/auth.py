import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os

def check_auth():
    # Cargar configuración
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    # El nuevo método login devuelve el estado directamente
    # La interfaz se dibuja sola
    authenticator.login()

    # Recuperamos los valores desde el estado de la sesión que maneja la librería
    auth_status = st.session_state.get("authentication_status")
    username = st.session_state.get("username")
    
    # Buscamos el nombre completo en el config usando el username
    name = None
    if auth_status and username:
        name = config['credentials']['usernames'][username]['name']

    # Guardamos el autenticador para poder hacer logout luego
    st.session_state['authenticator'] = authenticator

    return auth_status, name, username