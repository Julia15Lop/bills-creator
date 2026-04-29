import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
# Importamos nuestras funciones modulares
from src.engine import procesar_factura
from src.bills_gen import generar_ods

st.set_page_config(page_title="FactuPro Arturo Castro", layout="wide")

tallas_cols = ["T-34", "T-36", "T-38", "T-40", "T-42", "T-44"]

# --- CONFIGURACIÓN DE RUTAS ---
PATH_COUNTERS = 'data/counters.json'
PATH_PRECIOS = 'data/listado_precios_clientes.ods'
FOLDER_OUTPUT = 'output'

# Asegurar que las carpetas necesarias existen (Mentalidad SRE)
if not os.path.exists(FOLDER_OUTPUT):
    os.makedirs(FOLDER_OUTPUT)

if os.path.exists(PATH_COUNTERS):
    with open(PATH_COUNTERS, 'r', encoding='utf-8') as f:
        contadores = json.load(f)
else:
    st.error(f"Falta archivo crítico: {PATH_COUNTERS}")
    st.stop()

# --- LÓGICA DE RESET ---
if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

if 'df_pedido' not in st.session_state:
    st.session_state.df_pedido = pd.DataFrame(columns=["Nombre Prenda"] + tallas_cols)

def reset_todo():
    st.session_state.df_pedido = pd.DataFrame(columns=["Nombre Prenda"] + tallas_cols)
    st.session_state.reset_counter += 1
    st.rerun()

# --- PESTAÑAS ---
tab1, tab2 = st.tabs(["📄 Nueva Factura", "🏷️ Gestionar Precios"])

# ==========================================
# PESTAÑA 1: FACTURACIÓN
# ==========================================
with tab1:
    st.title("🚀 Generador de Facturas")
    
    with st.sidebar:
        st.header("⚙️ Configuración")
        emisor = st.selectbox("Emisor", ["Arturo", "Carmen"])
        cliente = st.selectbox("Cliente", ["belinda", "woven"])
        objetivo = st.number_input("Objetivo Presupuesto (€)", value=2500)
        fecha_selec = st.date_input("Fecha de Factura", datetime.now())
        fecha_str = fecha_selec.strftime('%d/%m/%Y')
        
        st.divider()
        st.button("🔄 Nueva Factura (Limpiar)", on_click=reset_todo, use_container_width=True)

    st.subheader("📦 Detalle del Pedido")
    
    pedido_editado = st.data_editor(
        st.session_state.df_pedido,
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_v_{st.session_state.reset_counter}", 
        column_config={
            "Nombre Prenda": st.column_config.TextColumn("Modelo / Referencia", width="large"),
            **{t: st.column_config.NumberColumn(t, min_value=0, default=0) for t in tallas_cols}
        }
    )

    # El botón ahora solo genera, no ofrece descarga
    if st.button("📊 Generar Factura", type="primary", use_container_width=True):
        
        prendas_dict = {}
        for _, fila in pedido_editado.iterrows():
            nombre = fila["Nombre Prenda"]
            if pd.isna(nombre) or str(nombre).strip() == "": continue
            
            t_dict = {t: int(fila[t]) for t in tallas_cols if pd.notna(fila[t]) and int(fila[t]) > 0}
            if t_dict:
                prendas_dict[str(nombre).strip().upper()] = t_dict

        if not prendas_dict:
            st.error("⚠️ No hay datos en la tabla para generar la factura.")
        else:
            with st.spinner("Procesando y guardando..."):
                # 1. Cargar precios
                df_p = pd.read_excel(PATH_PRECIOS, engine='odf')
                
                # 2. Calcular datos (engine.py)
                resultado = procesar_factura(emisor, cliente, fecha_str, objetivo, prendas_dict, df_p, contadores)
                
                # 3. Crear el ODS en la carpeta /output (bills_gen.py)
                ruta_final = generar_ods(resultado)
                
                # 4. Actualizar contadores
                contadores[emisor.lower()]['ultimo_numero'] = resultado['factura']
                with open(PATH_COUNTERS, 'w', encoding='utf-8') as f:
                    json.dump(contadores, f, indent=2)

                # Notificación visual
                st.success(f"✅ Factura Nº {resultado['factura']} guardada correctamente en: `{ruta_final}`")
                
                # Resumen de totales
                c1, c2 = st.columns(2)
                c1.metric("Total Final", f"{resultado['total_estimado']} €")
                if resultado['supera_objetivo']:
                    st.warning(f"⚠️ Atención: Se ha superado el objetivo de {objetivo}€")
                
                st.balloons()

# ==========================================
# PESTAÑA 2: GESTIÓN DE PRECIOS
# ==========================================
with tab2:
    st.title("🏷️ Gestión de Listado de Precios")
    
    if os.path.exists(PATH_PRECIOS):
        df_full = pd.read_excel(PATH_PRECIOS, engine='odf')
        
        st.subheader("🔍 Buscador")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            f_cli = st.multiselect("Filtrar por Cliente", options=df_full["ID_CLIENTE"].unique())
        with col_f2:
            f_nom = st.text_input("Buscar prenda por nombre")

        df_view = df_full.copy()
        if f_cli:
            df_view = df_view[df_view["ID_CLIENTE"].isin(f_cli)]
        if f_nom:
            df_view = df_view[df_view["NOMBRE ARTÍCULO"].str.contains(f_nom, case=False, na=False)]

        df_edit_p = st.data_editor(df_view, num_rows="dynamic", use_container_width=True, key="edit_precios")
        
        if st.button("💾 Guardar Cambios en Listado"):
            if f_cli or f_nom:
                df_full.update(df_edit_p)
                nuevos_registros = df_edit_p[~df_edit_p.index.isin(df_full.index)]
                df_final = pd.concat([df_full, nuevos_registros])
            else:
                df_final = df_edit_p

            df_final.to_excel(PATH_PRECIOS, engine='odf', index=False)
            st.success("¡Base de datos de precios actualizada!")
            st.rerun()