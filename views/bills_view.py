import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from src.engine import procesar_factura
from src.bills_gen import generar_ods

def render_bills_view(username):
    PATH_COUNTERS = 'data/counters.json'
    PATH_PRECIOS = 'data/listado_precios_clientes.xlsx' 
    TALLAS_COLS = ["T-34", "T-36", "T-38", "T-40", "T-42", "T-44"]

    # 1. Cargar contadores
    if not os.path.exists(PATH_COUNTERS):
        st.error(f"No se encuentra {PATH_COUNTERS}")
        return

    with open(PATH_COUNTERS, 'r', encoding='utf-8') as f:
        data_raw = json.load(f)
        contadores = {str(k).strip().lower(): v for k, v in data_raw.items()}

    def limpiar_campos():
        st.session_state.df_pedido = pd.DataFrame(columns=["Nombre Prenda"] + TALLAS_COLS)
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
        if st.button("➕ Nueva Factura", use_container_width=True):
            limpiar_campos()
            st.rerun()

    # 3. Tabla de Pedido
    st.write(f"### 📋 Pedido: {emisor_key.upper()}")
    
    if 'df_pedido' not in st.session_state:
        st.session_state.df_pedido = pd.DataFrame(columns=["Nombre Prenda"] + TALLAS_COLS)

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

    # 4. Botón Generar con los nombres de tus columnas reales
    if st.button("🚀 Generar Factura", type="primary", use_container_width=True):
        
        if not os.path.exists(PATH_PRECIOS):
            st.error(f"No se encuentra el archivo: {PATH_PRECIOS}")
            return

        df_p = pd.read_excel(PATH_PRECIOS)
        
        # --- TUS COLUMNAS REALES ---
        COL_NOMBRE_EXCEL = 'NOMBRE ARTÍCULO'
        COL_PRECIO_EXCEL = 'PRECIO CLIENTE'

        pedido_limpio = {}
        total_acumulado = 0.0
        prendas_sin_precio = []

        for _, row in pedido_editado.iterrows():
            nombre = row["Nombre Prenda"]
            if pd.isna(nombre) or str(nombre).strip() == "": continue
            
            nombre_clean = str(nombre).strip().upper()
            cantidades = {t: int(row[t] or 0) for t in TALLAS_COLS if int(row[t] or 0) > 0}
            
            if cantidades:
                pedido_limpio[nombre_clean] = cantidades
                
                # Buscamos la prenda en tu columna 'NOMBRE ARTÍCULO'
                match = df_p[df_p[COL_NOMBRE_EXCEL].astype(str).str.strip().str.upper() == nombre_clean]
                
                if not match.empty:
                    # Usamos tu columna 'PRECIO CLIENTE'
                    p_unitario = float(match.iloc[0][COL_PRECIO_EXCEL])
                    total_acumulado += sum(cantidades.values()) * p_unitario
                else:
                    prendas_sin_precio.append(nombre_clean)

        if not pedido_limpio:
            st.warning("⚠️ No hay cantidades en la tabla.")
        elif prendas_sin_precio:
            st.error(f"❌ No encontré el precio para: {', '.join(prendas_sin_precio)}")
            st.info("Asegúrate de que el nombre en la tabla sea IGUAL al del Excel.")
        else:
            try:
                st.divider()
                c1, c2 = st.columns([2, 1])
                
                with c2:
                    st.metric("PRECIO FINAL", f"{total_acumulado:,.2f} €")
                    if total_acumulado > objetivo:
                        st.warning(f"⚠️ ¡Ojo! Te has pasado del objetivo por {(total_acumulado - objetivo):.2f} €")

                # Generar Factura
                datos_fiscales = contadores[emisor_key]
                res = procesar_factura(emisor_key, cliente, fecha_str, objetivo, pedido_limpio, df_p, datos_fiscales)
                ruta = generar_ods(res)
                
                with c1:
                    st.success(f"✅ Factura Nº {res['factura']} generada.")
                    with open(ruta, "rb") as f:
                        st.download_button("📥 Descargar Factura", f, file_name=os.path.basename(ruta))
                
                # Actualizar JSON
                contadores[emisor_key]['ultimo_numero'] = res['factura']
                with open(PATH_COUNTERS, 'w', encoding='utf-8') as f:
                    json.dump(contadores, f, indent=2, ensure_ascii=False)
                
                st.balloons()
            except Exception as e:
                st.error(f"Error en el motor: {e}")