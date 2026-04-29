import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from src.engine import procesar_factura
from src.bills_gen import generar_ods

def render_bills_view(username):
    PATH_COUNTERS = 'data/counters.json'
    PATH_PRECIOS = 'data/listado_precios_clientes.ods'
    TALLAS_COLS = ["T-34", "T-36", "T-38", "T-40", "T-42", "T-44"]

    # 1. Cargar contadores
    with open(PATH_COUNTERS, 'r', encoding='utf-8') as f:
        data_raw = json.load(f)
        contadores = {str(k).strip().lower(): v for k, v in data_raw.items()}

    # --- FUNCIÓN PARA LIMPIAR CAMPOS ---
    def limpiar_campos():
        # Reseteamos el dataframe del pedido
        st.session_state.df_pedido = pd.DataFrame(columns=["Nombre Prenda"] + TALLAS_COLS)
        # Forzamos que el editor de datos se reinicie usando una clave dinámica
        if "editor_key_suffix" not in st.session_state:
            st.session_state.editor_key_suffix = 0
        st.session_state.editor_key_suffix += 1

    # 2. Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")
        user_id = str(username).strip().lower()
        emisor_key = user_id if user_id != "admin" else st.selectbox("Emisor:", list(contadores.keys()))
        
        cliente = st.selectbox("Cliente:", ["belinda", "woven"])
        objetivo = st.number_input("Objetivo (€):", value=2500)
        
        fecha_sel = st.date_input("Fecha:", datetime.now())
        fecha_str = fecha_sel.strftime('%d/%m/%y')
        
        st.divider()
        # BOTÓN NUEVA FACTURA
        if st.button("➕ Nueva Factura", use_container_width=True, help="Limpia todos los campos de la tabla"):
            limpiar_campos()
            st.rerun() # Recarga la app para aplicar la limpieza

    # 3. Tabla de Pedido
    st.write(f"### 📋 Pedido: {emisor_key.upper()}")
    
    if 'df_pedido' not in st.session_state:
        st.session_state.df_pedido = pd.DataFrame(columns=["Nombre Prenda"] + TALLAS_COLS)

    # Usamos un sufijo en la key para que Streamlit "olvide" los datos viejos al limpiar
    suffix = st.session_state.get("editor_key_suffix", 0)
    
    pedido_editado = st.data_editor(
        st.session_state.df_pedido,
        num_rows="dynamic",
        use_container_width=True,
        key=f"ed_{emisor_key}_{suffix}", 
        column_config={
            **{t: st.column_config.NumberColumn(t, min_value=0, default=0) for t in TALLAS_COLS}
        }
    )

    # 4. Botón Generar (Lógica igual a la anterior)
    if st.button("🚀 Generar Factura", type="primary", use_container_width=True):
        # ... (aquí va tu lógica de limpieza de 'pedido_limpio' y procesar_factura)
        # Al final de una generación exitosa, podrías llamar a limpiar_campos() si quieres que se borre sola
        
        pedido_limpio = {}
        for _, row in pedido_editado.iterrows():
            nombre = row["Nombre Prenda"]
            if pd.isna(nombre) or str(nombre).strip() == "": continue
            t_vals = {t: int(row[t] or 0) for t in TALLAS_COLS if int(row[t] or 0) > 0}
            if t_vals:
                pedido_limpio[str(nombre).strip().upper()] = t_vals

        if not pedido_limpio:
            st.warning("⚠️ No hay cantidades mayores a 0.")
        else:
            try:
                df_p = pd.read_excel(PATH_PRECIOS, engine='odf')
                datos_fiscales = contadores[emisor_key]
                res = procesar_factura(emisor_key, cliente, fecha_str, objetivo, pedido_limpio, df_p, datos_fiscales)
                ruta = generar_ods(res)
                
                # Actualizar JSON
                contadores[emisor_key]['ultimo_numero'] = res['factura']
                with open(PATH_COUNTERS, 'w', encoding='utf-8') as f:
                    json.dump(contadores, f, indent=2, ensure_ascii=False)
                
                st.success(f"✅ Factura Nº {res['factura']} generada.")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {e}")