import streamlit as st
import pandas as pd
from src.ms_graph import descargar_db_onedrive, subir_archivo_onedrive

def render_prices_view():
    st.subheader("🏷️ Listado de Precios")

    # Leer DB de OneDrive
    path_db = descargar_db_onedrive()
    xlsx = pd.ExcelFile(path_db)
    df_precios = pd.read_excel(xlsx, 'PRECIOS')
    df_contadores = pd.read_excel(xlsx, 'CONTADORES')

    # Filtros que ya tenías
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        clientes = ["Todos"] + sorted(df_precios['ID_CLIENTE'].unique().tolist())
        cliente_sel = st.selectbox("🎯 Filtrar Cliente:", clientes)
    with col_f2:
        busqueda = st.text_input("🔍 Buscar Modelo:", "")

    df_mostrar = df_precios.copy()
    if cliente_sel != "Todos":
        df_mostrar = df_mostrar[df_mostrar['ID_CLIENTE'] == cliente_sel]
    if busqueda:
        df_mostrar = df_mostrar[df_mostrar['NOMBRE ARTÍCULO'].str.contains(busqueda, case=False, na=False)]

    # Editor
    df_editado = st.data_editor(df_mostrar, use_container_width=True, num_rows="dynamic")

    if st.button("💾 Guardar Cambios", type="primary"):
        # Sincronizar cambios en el DataFrame original
        df_precios.update(df_editado)
        
        # Guardar archivo localmente
        with pd.ExcelWriter(path_db, engine='xlsxwriter') as writer:
            df_precios.to_excel(writer, sheet_name='PRECIOS', index=False)
            df_contadores.to_excel(writer, sheet_name='CONTADORES', index=False)
        
        # Subir a OneDrive
        subir_archivo_onedrive(path_db, "FactuPro_App", "FactuPro_DB.xlsx")
        st.success("✅ Listado de precios actualizado en la nube.")