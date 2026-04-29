import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os

def check_auth():
    # Cargar la configuración desde el YAML
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    with open(config_path) as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    # Renderizar el formulario de login
    name, authentication_status, username = authenticator.login('main')

    if authentication_status:
        # Si el login es correcto, guardamos el objeto en la sesión para usarlo luego
        st.session_state['authenticator'] = authenticator
        return True, name, username
    elif authentication_status == False:
        st.error('Usuario o contraseña incorrectos')
        return False, None, None
    elif authentication_status == None:
        st.warning('Por favor, introduce tus credenciales')
        return False, None, None