import streamlit as st
from src.auth import check_auth

# 1. Configuración de página (Debe ser la primera instrucción de Streamlit)
st.set_page_config(
    page_title="FactuPro ERP", 
    page_icon="🧵", 
    layout="wide"
)

# 2. Ejecutar Control de Seguridad
# Retorna el estado, el nombre completo y el ID de usuario del config.yaml
auth_status, user_full_name, username = check_auth()

if auth_status:
    # IMPORTANTE: Importamos las vistas aquí dentro para que no se ejecuten
    # si el usuario no está logueado (optimiza rendimiento y seguridad)
    from views.bills_view import render_bills_view
    from views.prices_view import render_prices_view

    # 3. Definición de Páginas
    # Usamos iconos de Material Design (opcional)
    pg_factura = st.Page(
        lambda: render_bills_view(username), 
        title="Generar Factura", 
        icon=":material/description:",
        default=True
    )
    
    pg_precios = st.Page(
        render_prices_view, 
        title="Gestionar Precios", 
        icon=":material/sell:"
    )

    # 4. Configuración de la Navegación
    # Esto crea secciones automáticas en el sidebar
    pg = st.navigation({
        "Operaciones": [pg_factura],
        "Administración": [pg_precios]
    })
    
    # 5. Sidebar personalizado
    with st.sidebar:
        st.title(f"👋 {user_full_name}")
        # El logout se integra perfectamente en el sidebar
        if 'authenticator' in st.session_state:
            st.session_state['authenticator'].logout('Cerrar Sesión', 'sidebar')
        st.divider()

    # 6. Ejecución de la página seleccionada
    pg.run()

elif auth_status is False:
    st.error('Usuario o contraseña incorrectos')
else:
    # auth_status es None cuando no se ha intentado login
    st.info('Por favor, introduzca sus credenciales para acceder al sistema.')