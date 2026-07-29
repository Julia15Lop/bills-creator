import streamlit as st
import pandas as pd
import os

def render_prices_view():
    PATH_PRECIOS = 'data/listado_precios_clientes.xlsx'
    st.subheader("🏷️ Listado de Precios")

    if not os.path.exists(PATH_PRECIOS):
        st.error(f"🚨 No se encuentra el archivo: {PATH_PRECIOS}")
        st.info("Asegúrate de que la carpeta 'data' existe y tiene el archivo .xlsx")
        return

    df_precios = pd.read_excel(PATH_PRECIOS)

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
                from src.utils import limpiar_precio
                
                # Obtener los cambios del editor de Streamlit
                state = st.session_state.get("editor_maestro_definitivo", {})
                
                if state:
                    # 1. Filas editadas
                    edited_rows = state.get("edited_rows", {})
                    for pos_str, changes in edited_rows.items():
                        pos = int(pos_str)
                        actual_idx = df_mostrar.index[pos]
                        for col, val in changes.items():
                            if col in ['PRECIO CLIENTE', 'PRECIO CONFECCIÓN']:
                                val = limpiar_precio(val)
                            df_precios.at[actual_idx, col] = val
                    
                    # 2. Filas eliminadas
                    deleted_rows = state.get("deleted_rows", {})
                    if deleted_rows:
                        indices_to_drop = [df_mostrar.index[pos] for pos in deleted_rows]
                        df_precios = df_precios.drop(index=indices_to_drop)
                    
                    # 3. Filas añadidas
                    added_rows = state.get("added_rows", {})
                    if added_rows:
                        for row in added_rows:
                            for col in ['PRECIO CLIENTE', 'PRECIO CONFECCIÓN']:
                                if col in row:
                                    row[col] = limpiar_precio(row[col])
                                else:
                                    row[col] = 0.0
                        df_added = pd.DataFrame(added_rows)
                        df_precios = pd.concat([df_precios, df_added], ignore_index=True)
                
                df_precios.to_excel(PATH_PRECIOS, engine='openpyxl', index=False)
                st.success("✅ Cambios guardados.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    with c2:
        csv = df_editado.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Excel", data=csv, file_name="precios.csv", use_container_width=True)

    with c3:
        html_table = df_editado.to_html(index=False, border=1)
        html_final = f"<html><style>table{{width:100%;border-collapse:collapse;}}th,td{{padding:8px;border:1px dotted #ccc;}}</style><body>{html_table}</body></html>"
        st.download_button("🖨️ PDF (HTML)", data=html_final, file_name="imprimir.html", mime="text/html", use_container_width=True)