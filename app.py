import streamlit as st
from src.auth import check_auth

# 1. Configuración de página
st.set_page_config(page_title="PatternBills Arturo Castro", page_icon="🧵", layout="wide")

# 2. Seguridad
auth_status, user_full_name, username = check_auth()

if auth_status:
    # Importación diferida para mejorar velocidad
    from views.bills_view import render_bills_view
    from views.prices_view import render_prices_view

    # 3. Sidebar: Usuario y Logout
    with st.sidebar:
        st.title(f"👋 {user_full_name}")
        st.session_state['authenticator'].logout('Cerrar Sesión', 'sidebar')
        st.divider()

    # 4. Diseño de Pestañas (Tabs) - El que te gusta
    tab_factura, tab_precios = st.tabs(["📄 Nueva Factura", "🏷️ Productos y Precios"])

    with tab_factura:
        render_bills_view(username)
        
    with tab_precios:
        render_prices_view()

elif auth_status is False:
    st.error('Usuario o contraseña incorrectos')
else:
    st.warning('Por favor, introduzca sus credenciales.')