import streamlit as st
import pandas as pd
import os

def render_prices_view():
    PATH_PRECIOS = 'data/listado_precios_clientes.ods'
    st.subheader("🏷️ Maestro de Precios")

    if not os.path.exists(PATH_PRECIOS):
        st.error(f"🚨 No se encuentra el archivo: {PATH_PRECIOS}")
        st.info("Asegúrate de que la carpeta 'data' existe y tiene el archivo .ods")
        return

    df_precios = pd.read_excel(PATH_PRECIOS, engine='odf')

    # --- FILTROS SUPERIORES ---
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        clientes_disp = ["Todos"] + sorted(list(df_precios['ID_CLIENTE'].unique()))
        cliente_sel = st.selectbox("🎯 Filtrar por Cliente:", clientes_disp)
    
    with col_f2:
        busqueda = st.text_input("🔍 Buscar Modelo/Referencia:", "")

    # Aplicar filtros a la copia de visualización
    df_mostrar = df_precios.copy()
    if cliente_sel != "Todos":
        df_mostrar = df_mostrar[df_mostrar['ID_CLIENTE'] == cliente_sel]
    if busqueda:
        df_mostrar = df_mostrar[df_mostrar['NOMBRE ARTÍCULO'].str.contains(busqueda, case=False, na=False)]

    # --- TABLA EDITABLE CON FILTROS INTERNOS ---
    st.caption("💡 También puedes filtrar por Categoría o Colección en los iconos 🔍 de la tabla.")
    df_editado = st.data_editor(
        df_mostrar, 
        use_container_width=True, 
        num_rows="dynamic",
        key="editor_maestro_definitivo"
    )

    # --- BOTONES ---
    st.divider()
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("💾 Guardar Cambios", type="primary", use_container_width=True):
            try:
                # Actualizamos el original con lo editado
                df_precios.update(df_editado)
                # Si hay filas nuevas, las añadimos al final
                if len(df_editado) > len(df_mostrar):
                    nuevas = df_editado.iloc[len(df_mostrar):]
                    df_precios = pd.concat([df_precios, nuevas], ignore_index=True)
                
                df_precios.to_excel(PATH_PRECIOS, engine='odf', index=False)
                st.success("✅ Cambios guardados.")
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    with c2:
        csv = df_editado.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Excel", data=csv, file_name="precios.csv", use_container_width=True)

    with c3:
        html_table = df_editado.to_html(index=False, border=1)
        html_final = f"<html><style>table{{width:100%;border-collapse:collapse;}}th,td{{padding:8px;border:1px dotted #ccc;}}</style><body>{html_table}</body></html>"
        st.download_button("🖨️ PDF (HTML)", data=html_final, file_name="imprimir.html", mime="text/html", use_container_width=True)