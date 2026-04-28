import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import subprocess

# Configuración de la página
st.set_page_config(page_title="FactuPro Arturo & Carmen", layout="wide")

# --- LÓGICA DE ESTADO (PERSISTENCIA) ---
tallas_cols = ["T-34", "T-36", "T-38", "T-40", "T-42", "T-44"]

if 'df_pedido' not in st.session_state:
    # Inicializamos la tabla vacía con las columnas de tallas
    st.session_state.df_pedido = pd.DataFrame(columns=["Nombre Prenda"] + tallas_cols)

def reset_todo():
    # Función para limpiar el formulario
    st.session_state.df_pedido = pd.DataFrame(columns=["Nombre Prenda"] + tallas_cols)
    st.rerun()

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2 = st.tabs(["📄 Nueva Factura", "🏷️ Gestionar Precios"])

# ==========================================
# PESTAÑA 1: GENERACIÓN DE FACTURAS
# ==========================================
with tab1:
    st.title("🚀 Generador de Facturas Inteligente")
    
    with st.sidebar:
        st.header("⚙️ Configuración")
        emisor = st.selectbox("Selecciona Emisor", ["Arturo", "Carmen"])
        
        # Corrección de Clientes: belinda o woven
        cliente = st.selectbox("Selecciona Cliente", ["belinda", "woven"])
        
        objetivo = st.number_input("Objetivo Presupuesto (€)", value=2500)
        
        # Gestión de Fecha (Blindada para evitar errores de formato)
        fecha_selec = st.date_input("Fecha de Factura", datetime.now())
        fecha_str = fecha_selec.strftime('%d/%m/%Y')
        
        st.divider()
        if st.button("🔄 Resetear Formulario", use_container_width=True):
            reset_todo()

    st.subheader("📦 Detalle del Pedido")
    st.info("Escribe el nombre del modelo y rellena las cantidades. Las tallas vacías o con 0 se ignorarán.")
    
    # Editor de datos tipo Excel (Matriz de tallas)
    # Se eliminó 'placeholder' para evitar errores en versiones antiguas de Streamlit
    pedido_editado = st.data_editor(
        st.session_state.df_pedido,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Nombre Prenda": st.column_config.TextColumn("Nombre del Modelo", width="large"),
            **{t: st.column_config.NumberColumn(t, min_value=0, default=0, format="%d") for t in tallas_cols}
        }
    )

    if st.button("📊 Generar Factura Final", type="primary", use_container_width=True):
        # 1. Transformar tabla a formato JSON compatible con los scripts
        prendas_json = {}
        for _, fila in pedido_editado.iterrows():
            nombre = fila["Nombre Prenda"]
            if pd.isna(nombre) or str(nombre).strip() == "": 
                continue
            
            tallas_dict = {}
            for t in tallas_cols:
                # Solo incluimos tallas con unidades > 0
                val = int(fila[t]) if pd.notna(fila[t]) else 0
                if val > 0:
                    tallas_dict[t] = val
            
            if tallas_dict:
                prendas_json[str(nombre).strip().upper()] = tallas_dict

        # 2. Validar si hay datos
        if not prendas_json:
            st.error("⚠️ Error: No has introducido ninguna prenda o cantidad válida.")
        else:
            # 3. Crear el archivo input.txt para comunicación interna
            input_content = (
                f"Emisor: {emisor.lower()}\n"
                f"Cliente: {cliente}\n"
                f"Fecha: {fecha_str}\n"
                f"Objetivo: {objetivo}\n"
                f"Prendas: {json.dumps(prendas_json)}"
            )
            
            with open("input.txt", "w", encoding="utf-8") as f:
                f.write(input_content)

            # 4. Ejecutar procesos en segundo plano
            with st.spinner("Calculando y generando archivo ODS..."):
                try:
                    # Motor de cálculo
                    subprocess.run(["python", "mcp_facturacion.py"], check=True)
                    # Relleno de plantilla
                    subprocess.run(["python", "completar_ods.py"], check=True)
                    
                    # Leer resultados del JSON intermedio
                    if os.path.exists("ultimo_resultado.json"):
                        with open("ultimo_resultado.json", "r", encoding="utf-8") as r:
                            res = json.load(r)
                        
                        st.success(f"✅ Factura Nº {res['factura']} generada correctamente.")
                        
                        col_res1, col_res2 = st.columns(2)
                        col_res1.metric("Total Factura (IVA incl.)", f"{res['total_estimado']} €")
                        
                        if res['supera_objetivo']:
                            st.warning(f"⚠️ El total supera el objetivo de {objetivo}€")
                        else:
                            st.info("👍 El total está dentro del presupuesto.")
                            
                        st.balloons()
                    else:
                        st.error("Error: El motor de cálculo no generó el archivo de resultados.")
                        
                except Exception as e:
                    st.error(f"Ocurrió un error técnico: {str(e)}")

# ==========================================
# PESTAÑA 2: GESTIÓN DE PRECIOS
# ==========================================
with tab2:
    st.title("🏷️ Gestión del Listado de Precios")
    st.write("Edita directamente los precios o añade nuevas prendas aquí. No olvides pulsar 'Guardar'.")
    
    archivo_precios = 'listado_precios_clientes.ods'
    
    if os.path.exists(archivo_precios):
        df_precios = pd.read_excel(archivo_precios, engine='odf')
        
        # Editor interactivo para el listado oficial
        df_editado_precios = st.data_editor(
            df_precios, 
            num_rows="dynamic", 
            use_container_width=True,
            key="editor_precios"
        )
        
        if st.button("💾 Guardar Cambios en el Listado Oficial"):
            try:
                # Guardamos los cambios de vuelta al ODS
                df_editado_precios.to_excel(archivo_precios, engine='odf', index=False)
                st.success("¡Archivo 'listado_precios_clientes.ods' actualizado con éxito!")
            except Exception as e:
                st.error(f"Error al guardar: {e}")
    else:
        st.error(f"No se encuentra el archivo {archivo_precios} en la carpeta.")