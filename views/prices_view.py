import streamlit as st
import pandas as pd
import os

def render_prices_view():
    st.subheader("🏷️ Gestión de Listado de Precios")
    PATH_PRECIOS = 'data/listado_precios_clientes.ods'

    if not os.path.exists(PATH_PRECIOS):
        st.error("No se encontró el archivo de precios en data/")
        return

    # Cargar Excel Maestro
    df_full = pd.read_excel(PATH_PRECIOS, engine='odf')

    # Filtros de búsqueda
    col1, col2 = st.columns(2)
    with col1:
        f_cli = st.multiselect("Filtrar por Cliente:", options=df_full["ID_CLIENTE"].unique() if "ID_CLIENTE" in df_full.columns else [])
    with col2:
        f_nom = st.text_input("Buscar prenda por nombre:")

    # Aplicar Filtros
    df_view = df_full.copy()
    if f_cli:
        df_view = df_view[df_view["ID_CLIENTE"].isin(f_cli)]
    if f_nom:
        df_view = df_view[df_view["NOMBRE ARTÍCULO"].str.contains(f_nom, case=False, na=False)]

    # Editor de datos
    st.info("💡 Puedes editar precios o añadir filas aquí debajo.")
    df_edit = st.data_editor(df_view, num_rows="dynamic", use_container_width=True)

    # Guardar cambios
    if st.button("💾 Guardar Cambios en Maestro"):
        try:
            # Sincronizar cambios con el dataframe original (por si había filtros)
            if f_cli or f_nom:
                df_full.update(df_edit)
                nuevas_filas = df_edit[~df_edit.index.isin(df_full.index)]
                df_final = pd.concat([df_full, nuevas_filas])
            else:
                df_final = df_edit

            df_final.to_excel(PATH_PRECIOS, engine='odf', index=False)
            st.success("¡Base de datos de precios actualizada correctamente!")
        except Exception as e:
            st.error(f"Error al guardar: {e}")