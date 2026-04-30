import streamlit as st
import pandas as pd
import json
from datetime import datetime
from src.ms_graph import descargar_db_onedrive, subir_archivo_onedrive
from src.engine import procesar_factura
from src.bills_gen import generar_ods # Tu generador basado en plantilla

def render_bills_view(username):
    # 1. Sincronizar con OneDrive
    with st.spinner("Sincronizando con OneDrive..."):
        path_db = descargar_db_onedrive()
        xlsx = pd.ExcelFile(path_db)
        df_precios = pd.read_excel(xlsx, 'PRECIOS')
        df_contadores = pd.read_excel(xlsx, 'CONTADORES')

    TALLAS_COLS = ["T-34", "T-36", "T-38", "T-40", "T-42", "T-44"]

    with st.sidebar:
        st.header("⚙️ Configuración")
        user_id = str(username).strip().lower()
        emisor_key = user_id if user_id != "admin" else st.selectbox("Emisor:", df_contadores['Usuario'].tolist())
        
        # Datos Fiscales desde Secrets
        fiscal = st.secrets["emisores"][emisor_key]
        # Número desde el Excel de OneDrive
        num_actual = int(df_contadores.loc[df_contadores['Usuario'] == emisor_key, 'Ultimo_Numero'].values[0])
        
        datos_fiscales = {**fiscal, "ultimo_numero": num_actual}
        
        st.info(f"Factura actual: **{num_actual + 1}**")
        cliente = st.selectbox("Cliente:", ["belinda", "woven"])
        fecha_sel = st.date_input("Fecha:", datetime.now())

    # --- Lógica de la Tabla de Pedido (Sin cambios de funcionalidad) ---
    st.write(f"### 📋 Pedido para {cliente.upper()}")
    if 'df_pedido' not in st.session_state:
        st.session_state.df_pedido = pd.DataFrame(columns=["Nombre Prenda"] + TALLAS_COLS)

    pedido_editado = st.data_editor(st.session_state.df_pedido, num_rows="dynamic", use_container_width=True)

    if st.button("🚀 Generar y Guardar en OneDrive", type="primary"):
        # 1. Procesar cálculos
        res = procesar_factura(emisor_key, cliente, fecha_sel.strftime('%d/%m/%y'), 2500, pedido_editado, df_precios, datos_fiscales)
        
        # 2. Generar archivo local
        ruta_ods = generar_ods(res) 
        
        # 3. SUBIR A ONEDRIVE
        año_mes = fecha_sel.strftime("%Y/%m") # Carpeta 2024/Mayo
        nombre_fich = f"Factura_{res['factura']}_{cliente}.xlsx"
        subir_archivo_onedrive(ruta_ods, f"FactuPro_App/Facturas/{año_mes}", nombre_fich)
        
        # 4. Actualizar el Excel Maestro en OneDrive
        df_contadores.loc[df_contadores['Usuario'] == emisor_key, 'Ultimo_Numero'] += 1
        with pd.ExcelWriter(path_db, engine='xlsxwriter') as writer:
            df_precios.to_excel(writer, sheet_name='PRECIOS', index=False)
            df_contadores.to_excel(writer, sheet_name='CONTADORES', index=False)
        
        # Subir de nuevo el maestro actualizado
        subir_archivo_onedrive(path_db, "FactuPro_App", "FactuPro_DB.xlsx")
        
        st.success(f"✅ Factura {res['factura']} subida a OneDrive y contador actualizado.")
        st.balloons()