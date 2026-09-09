import streamlit as st
import pandas as pd
from src.db import get_precios_df, save_precios_df, delete_precio_by_id

def render_prices_view():
    st.subheader("🏷️ Listado de Precios")

    try:
        df_precios = get_precios_df()
    except Exception as e:
        st.error(f"Error al cargar la tabla de precios: {e}")
        return

    if df_precios.empty:
        st.info("ℹ️ No hay registros en el catálogo de precios de Supabase.")
        return

    # Renombrado dinámico para mantener compatibilidad visual
    col_map = {
        "codigo_articulo": "CÓDIGO",
        "coleccion": "COLECCIÓN",
        "nombre_articulo": "NOMBRE ARTÍCULO",
        "categoria": "CATEGORÍA",
        "id_cliente": "ID_CLIENTE",
        "precio_cliente": "PRECIO CLIENTE",
        "precio_confeccion": "PRECIO CONFECCIÓN"
    }
    
    df_precios_renamed = df_precios.rename(columns=col_map)

    # --- FILTROS SUPERIORES ---
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        clientes_disp = ["Todos"] + sorted(list(df_precios_renamed['ID_CLIENTE'].dropna().unique()))
        cliente_sel = st.selectbox("🎯 Filtrar por Cliente:", clientes_disp)
    
    with col_f2:
        busqueda = st.text_input("🔍 Buscar Modelo/Referencia:", "")

    df_mostrar = df_precios_renamed.copy()
    if cliente_sel != "Todos":
        df_mostrar = df_mostrar[df_mostrar['ID_CLIENTE'] == cliente_sel]
    if busqueda and "NOMBRE ARTÍCULO" in df_mostrar.columns:
        df_mostrar = df_mostrar[df_mostrar['NOMBRE ARTÍCULO'].str.contains(busqueda, case=False, na=False)]

    # Mantenemos 'id' internamente pero excluimos 'user_key' y 'created_at' de la vista
    cols_visibles = [c for c in df_mostrar.columns if c not in ['user_key', 'created_at']]

    # reset_index(drop=True) para que Streamlit no arroje warnings con hide_index=True
    df_editor_input = df_mostrar[cols_visibles].reset_index(drop=True)

    st.caption("💡 Puedes editar precios directamente o filtrar usando las herramientas de la tabla.")
    df_editado = st.data_editor(
        df_editor_input,
        hide_index=True,  # Oculta el índice lateral 0, 1, 2...
        use_container_width=True, 
        num_rows="dynamic",
        key="editor_maestro_definitivo",
        column_config={
            "id": None  # Oculta la columna ID visualmente pero conserva los datos internamente
        }
    )

    st.divider()
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("💾 Guardar Cambios en Supabase", type="primary", use_container_width=True):
            try:
                # 1. Detectar productos borrados con la papelera
                if 'id' in df_editor_input.columns and 'id' in df_editado.columns:
                    ids_originales = set(df_editor_input['id'].dropna().astype(int))
                    ids_editados = set(df_editado['id'].dropna().astype(int))
                    ids_borrados = ids_originales - ids_editados
                    
                    for pid in ids_borrados:
                        delete_precio_by_id(pid)

                # 2. Revertir los nombres para sincronizar con la base de datos
                rev_map = {v: k for k, v in col_map.items()}
                df_to_save = df_editado.rename(columns=rev_map)

                save_precios_df(df_to_save)
                st.success("✅ Precios guardados exitosamente en Supabase.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    with c2:
        csv = df_editado.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Excel / CSV", data=csv, file_name="precios_supabase.csv", mime="text/csv", use_container_width=True)

    with c3:
        html_table = df_editado.to_html(index=False, border=1)
        html_final = f"<html><style>table{{width:100%;border-collapse:collapse;}}th,td{{padding:8px;border:1px dotted #ccc;}}</style><body>{html_table}</body></html>"
        st.download_button("🖨️ PDF (HTML)", data=html_final, file_name="imprimir.html", mime="text/html", use_container_width=True)