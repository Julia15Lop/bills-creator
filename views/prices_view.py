import streamlit as st
import pandas as pd
from src.db import get_precios_df, save_precios_df

def render_prices_view():
    st.subheader("🏷️ Listado de Precios")

    try:
        df_precios = get_precios_df()
    except Exception as e:
        st.error(f"Error al cargar la tabla de precios: {e}")
        return

    # Mapeo de columnas de Supabase a nombres para pantalla
    col_map = {
        "codigo_articulo": "CÓDIGO",
        "coleccion": "COLECCIÓN",
        "nombre_articulo": "NOMBRE ARTÍCULO",
        "categoria": "CATEGORÍA",
        "id_cliente": "CLIENTE",
        "precio_cliente": "PRECIO CLIENTE (€)",
        "precio_confeccion": "PRECIO CONFECCIÓN (€)"
    }
    
    if not df_precios.empty:
        df_renamed = df_precios.rename(columns=col_map)
    else:
        # Si la tabla está vacía, generamos la estructura básica
        df_renamed = pd.DataFrame(columns=["id", "user_key"] + list(col_map.values()))

    # --- 1. ORDENACIÓN LIMPIA ---
    if "COLECCIÓN" in df_renamed.columns and not df_renamed.empty:
        df_renamed = df_renamed.sort_values(by=["COLECCIÓN", "NOMBRE ARTÍCULO"], ascending=True).reset_index(drop=True)

    # --- 2. FILTROS ---
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        clientes_disp = ["Todos"] + sorted([str(c) for c in df_renamed['CLIENTE'].dropna().unique() if c])
        cliente_sel = st.selectbox("🎯 Filtrar por Cliente:", clientes_disp, key="pv_filtro_cli")
    
    with col_f2:
        busqueda = st.text_input("🔍 Buscar Modelo/Referencia:", "", key="pv_filtro_busq")

    df_mostrar = df_renamed.copy()
    if cliente_sel != "Todos":
        df_mostrar = df_mostrar[df_mostrar['CLIENTE'] == cliente_sel]
    if busqueda and "NOMBRE ARTÍCULO" in df_mostrar.columns:
        df_mostrar = df_mostrar[df_mostrar['NOMBRE ARTÍCULO'].str.contains(busqueda, case=False, na=False)]

    # --- 3. CONFIGURACIÓN DE COLUMNAS VISIBLES (OCULTAR ID) ---
    # Mantenemos 'id' en la estructura interna de df_mostrar pero indicamos a column_order que solo renderice las visibles
    cols_pantalla = [c for c in df_mostrar.columns if c not in ['id', 'user_key', 'created_at']]

    st.caption("💡 Puedes editar registros o pulsar el botón '+' al final de la tabla para agregar un nuevo producto.")
    
    # Editor interactivo
    df_editado = st.data_editor(
        df_mostrar,
        column_order=cols_pantalla,  # <-- Oculta 'id' visualmente
        use_container_width=True, 
        num_rows="dynamic",           # <-- Permite agregar nuevas filas con el '+'
        key="pv_editor_definitivo",
        column_config={
            "PRECIO CLIENTE (€)": st.column_config.NumberColumn("PRECIO CLIENTE (€)", format="%.2f €", default=0.0),
            "PRECIO CONFECCIÓN (€)": st.column_config.NumberColumn("PRECIO CONFECCIÓN (€)", format="%.2f €", default=0.0),
            "NOMBRE ARTÍCULO": st.column_config.TextColumn("NOMBRE ARTÍCULO", required=True)
        }
    )

    st.divider()
    c1, c2 = st.columns(2)

    with c1:
        if st.button("💾 Guardar Cambios en Supabase", type="primary", use_container_width=True, key="pv_btn_guardar_definitivo"):
            try:
                # Invertir nombres para enviarlos a las columnas de Supabase
                rev_map = {v: k for k, v in col_map.items()}
                df_to_save = df_editado.rename(columns=rev_map)

                save_precios_df(df_to_save)
                st.success("✅ Precios y nuevos productos guardados con éxito en Supabase.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    with c2:
        csv = df_editado[cols_pantalla].to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Exportar Catálogo a CSV", data=csv, file_name="catalogo_precios.csv", mime="text/csv", use_container_width=True, key="pv_btn_csv_definitivo")