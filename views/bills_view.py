import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from src.engine import procesar_factura
from src.bills_gen import generar_ods

def render_bills_view(username):
    # --- CONFIGURACIÓN DE RUTAS Y CONSTANTES ---
    PATH_COUNTERS = 'data/counters.json'
    PATH_PRECIOS = 'data/listado_precios_clientes.ods'
    TALLAS_COLS = ["T-34", "T-36", "T-38", "T-40", "T-42", "T-44"]

    st.subheader("📄 Generación de Factura")

    # 1. Cargar y normalizar contadores (SRE Best Practice para evitar errores de mayúsculas)
    if os.path.exists(PATH_COUNTERS):
        with open(PATH_COUNTERS, 'r', encoding='utf-8') as f:
            data_raw = json.load(f)
            contadores = {k.lower(): v for k, v in data_raw.items()}
    else:
        st.error("No se encontró data/counters.json")
        return

    # 2. Lógica de selección de Emisor (Admin vs Usuario)
    with st.sidebar:
        st.header("⚙️ Ajustes")
        if username.lower() == "admin":
            emisor_key = st.selectbox(
                "Gestionar emisor:", 
                options=list(contadores.keys()), 
                format_func=lambda x: x.capitalize()
            )
        else:
            emisor_key = username.lower()
            st.info(f"Emisor: **{emisor_key.capitalize()}**")

        cliente = st.selectbox("Cliente:", ["belinda", "woven"])
        objetivo = st.number_input("Objetivo Presupuesto (€):", value=2500)
        fecha_sel = st.date_input("Fecha Factura:", datetime.now())
        fecha_str = fecha_sel.strftime('%d/%m/%Y')

    # 3. Tabla de Pedido
    if 'df_pedido' not in st.session_state:
        st.session_state.df_pedido = pd.DataFrame(columns=["Nombre Prenda"] + TALLAS_COLS)

    st.write(f"### Pedido actual para {emisor_key.capitalize()}")
    pedido_editado = st.data_editor(
        st.session_state.df_pedido,
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_{emisor_key}"
    )

    # 4. Botón de Procesar
    if st.button("🚀 Generar Factura ODS", type="primary", use_container_width=True):
        pedido_limpio = {}
        for _, row in pedido_editado.iterrows():
            nombre = row["Nombre Prenda"]
            if pd.isna(nombre) or str(nombre).strip() == "": continue
            
            cantidades = {t: int(row[t]) for t in TALLAS_COLS if pd.notna(row[t]) and int(row[t]) > 0}
            if cantidades:
                pedido_limpio[str(nombre).strip().upper()] = cantidades

        if not pedido_limpio:
            st.error("⚠️ La tabla está vacía o no tiene cantidades válidas.")
        else:
            with st.spinner("Calculando y generando archivo..."):
                try:
                    df_p = pd.read_excel(PATH_PRECIOS, engine='odf')
                    datos_emisor = contadores[emisor_key]
                    
                    # Llamada al motor y al generador
                    res = procesar_factura(emisor_key, cliente, fecha_str, objetivo, pedido_limpio, df_p, datos_emisor)
                    ruta = generar_ods(res)
                    
                    # Actualizar contador en el JSON
                    contadores[emisor_key]['ultimo_numero'] = res['factura']
                    with open(PATH_COUNTERS, 'w', encoding='utf-8') as f:
                        json.dump(contadores, f, indent=2, ensure_ascii=False)
                    
                    st.success(f"✅ Factura Nº {res['factura']} guardada en `output/`")
                    st.info(f"Archivo: `{ruta}`")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")