import streamlit as st
import pandas as pd
import os

def render_prices_view():
    PATH_PRECIOS = 'data/listado_precios_clientes.ods'
    st.subheader("🏷️ Maestro de Precios")

    if not os.path.exists(PATH_PRECIOS):
        st.error("No se encuentra el archivo de precios.")
        return

    # 1. Carga de datos
    df_precios = pd.read_excel(PATH_PRECIOS, engine='odf')

    # 2. Filtros Externos (Buscador general)
    busqueda = st.text_input("🔍 Buscador rápido (Modelo o Referencia):", "")
    
    df_mostrar = df_precios.copy()
    if busqueda:
        df_mostrar = df_mostrar[df_mostrar['NOMBRE ARTÍCULO'].str.contains(busqueda, case=False, na=False)]

    # 3. EL EDITOR CON FILTROS EN CABECERAS
    st.info("💡 Haz clic en la lupa 🔍 de cualquier cabecera (Colección, Categoría, etc.) para filtrar la tabla.")
    
    # Configuramos las columnas para que sean interactivas
    df_editado = st.data_editor(
        df_mostrar, 
        use_container_width=True, 
        num_rows="dynamic",
        key="editor_interactivo",
        column_config={
            "COLECCIÓN": st.column_config.SelectboxColumn("Colección", options=list(df_precios['COLECCIÓN'].unique()) if 'COLECCIÓN' in df_precios else []),
            "CATEGORÍA": st.column_config.SelectboxColumn("Categoría", options=list(df_precios['CATEGORÍA'].unique()) if 'CATEGORÍA' in df_precios else []),
            "PRECIO CLIENTE": st.column_config.NumberColumn("Precio (€)", format="%.2f €"),
        }
    )

    # 4. BOTONES DE ACCIÓN
    st.divider()
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("💾 Guardar Cambios", type="primary", use_container_width=True):
            try:
                # Sincronización robusta
                df_precios.update(df_editado)
                if len(df_editado) > len(df_mostrar):
                    nuevas = df_editado.iloc[len(df_mostrar):]
                    df_precios = pd.concat([df_precios, nuevas], ignore_index=True)
                
                df_precios.to_excel(PATH_PRECIOS, engine='odf', index=False)
                st.success("✅ Guardado correctamente.")
            except Exception as e:
                st.error(f"Error: {e}")

    with c2:
        csv = df_editado.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Exportar Excel", data=csv, file_name="precios_export.csv", use_container_width=True)

    with c3:
        html_table = df_editado.to_html(index=False, border=1)
        html_final = f"<html><style>table{{width:100%;border-collapse:collapse;font-family:sans-serif;}}th,td{{padding:8px;border:1px solid #ccc;}}th{{background:#eee;}}</style><body>{html_table}</body></html>"
        st.download_button("🖨️ Generar PDF", data=html_final, file_name="imprimir.html", mime="text/html", use_container_width=True)