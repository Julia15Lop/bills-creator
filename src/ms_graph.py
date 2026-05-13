import os
import streamlit as st
from O365 import Account, FileSystemTokenBackend

@st.cache_resource
def get_account():
    """Crea y cachea la instancia de Account para mantener el flujo de MSAL vivo"""
    client_id = st.secrets["microsoft"]["client_id"]
    tenant_id = st.secrets["microsoft"].get("tenant_id", "common")
    credentials = (client_id, None)
    token_backend = FileSystemTokenBackend(token_path='.', token_filename='o365_token.txt')
    
    return Account(
        credentials, 
        tenant_id=tenant_id, 
        token_backend=token_backend
    )

def autenticar_microsoft():
    """Establece la conexión con Microsoft Graph de forma no bloqueante"""
    account = get_account()
    if account.is_authenticated:
        return account
    
    # Si no está autenticado, el backend intentará cargar el token del archivo automáticamente.
    # Si aún así no es válido, devolvemos None.
    return account if account.is_authenticated else None

def obtener_url_auth():
    """Genera la URL de autenticación usando la instancia cacheada"""
    account = get_account()
    scopes = ['Files.ReadWrite.All', 'Sites.ReadWrite.All', 'User.Read']
    redirect_uri = "https://login.microsoftonline.com/common/oauth2/nativeclient"
    
    url, state = account.con.get_authorization_url(
        requested_scopes=scopes, 
        redirect_uri=redirect_uri
    )
    return url, state

def finalizar_autenticacion(auth_url, state):
    """Completa el proceso usando la misma instancia de Account (vía cache)"""
    try:
        account = get_account()
        redirect_uri = "https://login.microsoftonline.com/common/oauth2/nativeclient"
        
        # El 'state' (flow) debe ser el mismo que devolvió get_authorization_url
        result = account.con.request_token(auth_url, state=state, redirect_uri=redirect_uri)
        return result
    except Exception as e:
        st.error(f"Error crítico en finalizar_autenticacion: {e}")
        import traceback
        st.error(traceback.format_exc())
        return False

def descargar_db_onedrive(nombre_archivo="listado_precios_clientes.xlsx"):
    """Descarga el Excel de OneDrive y devuelve la ruta del archivo local"""
    try:
        account = autenticar_microsoft()
        if not account:
            return None
            
        storage = account.storage()
        drive = storage.get_default_drive()
        
        items = drive.search(nombre_archivo)
        for item in items:
            if item.name == nombre_archivo:
                # Descarga el archivo en el directorio actual
                item.download(to_path='.')
                return nombre_archivo
        
        st.error(f"No se encontró el archivo '{nombre_archivo}' en OneDrive.")
        return None
    except Exception as e:
        st.error(f"Error detallado al descargar de OneDrive: {type(e).__name__}: {e}")
        return None

def subir_archivo_onedrive(ruta_local, carpeta_destino="FactuPro_App", nombre_final=None):
    """Sube un archivo local a una carpeta específica de OneDrive"""
    try:
        account = autenticar_microsoft()
        if not account:
            return False
            
        storage = account.storage()
        drive = storage.get_default_drive()
        
        root = drive.get_root_folder()
        
        # Intentar navegar a la carpeta destino
        try:
            target_folder = root.get_item(carpeta_destino)
        except Exception as folder_err:
            st.info(f"Carpeta '{carpeta_destino}' no encontrada, subiendo a la raíz. (Error: {folder_err})")
            target_folder = root
            
        if nombre_final:
            target_folder.upload(ruta_local, item_name=nombre_final)
        else:
            target_folder.upload(ruta_local)
        return True
    except Exception as e:
        st.error(f"Error detallado al subir a OneDrive: {type(e).__name__}: {e}")
        return False