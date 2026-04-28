import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import subprocess

st.set_page_config(page_title="FactuPro Arturo & Carmen", layout="wide")

tallas_cols = ["T-34", "T-36", "T-38", "T-40", "T-42", "T-44"]

if 'df_pedido' not in st.session_state:
    st.session_state.df_pedido = pd.DataFrame(columns=["Nombre Prenda"] + tallas_cols)

def reset_todo():
    st.session_state.df_pedido = pd.DataFrame(columns=["Nombre Prenda"] + tallas_cols)
    st.rerun()

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
        if st.button("🔄 Resetear Formulario"): reset_todo()

    st.subheader("📦 Detalle del Pedido")
    pedido_editado = st.data_editor(
        st.session_state.df_pedido,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Nombre Prenda": st.column_config.TextColumn("Modelo", width="large"),
            **{t: st.column_config.NumberColumn(t, min_value=0, default=0) for t in tallas_cols}
        }
    )

    if st.button("📊 Generar Factura Final", type="primary"):
        if os.path.exists("ultimo_resultado.json"): os.remove("ultimo_resultado.json")
        
        prendas_json = {}
        for _, fila in pedido_editado.iterrows():
            nombre = fila["Nombre Prenda"]
            if pd.isna(nombre) or str(nombre).strip() == "": continue
            tallas_dict = {t: int(fila[t]) for t in tallas_cols if pd.notna(fila[t]) and int(fila[t]) > 0}
            if tallas_dict: prendas_json[str(nombre).strip().upper()] = tallas_dict

        if not prendas_json:
            st.error("⚠️ No hay datos válidos.")
        else:
            input_content = f"Emisor: {emisor}\nCliente: {cliente}\nFecha: {fecha_str}\nObjetivo: {objetivo}\nPrendas: {json.dumps(prendas_json)}"
            with open("input.txt", "w", encoding="utf-8") as f: f.write(input_content)

            with st.spinner("Procesando..."):
                subprocess.run(["python", "mcp_facturacion.py"])
                subprocess.run(["python", "completar_ods.py"])
            
            if os.path.exists("ultimo_resultado.json"):
                with open("ultimo_resultado.json", "r", encoding="utf-8") as r:
                    res = json.load(r)
                st.success(f"✅ Factura Nº {res['factura']} generada.")
                st.metric("Total (IVA incl.)", f"{res['total_estimado']} €")
                st.balloons()
            else:
                st.error("Error en el motor de cálculo.")

# ==========================================
# PESTAÑA 2: LISTADO CON FILTROS
# ==========================================
with tab2:
    st.title("🏷️ Gestión de Listado de Precios")
    
    if os.path.exists('listado_precios_clientes.ods'):
        # Cargar datos originales
        df_p = pd.read_excel('listado_precios_clientes.ods', engine='odf')
        
        # --- BLOQUE DE FILTROS ---
        st.subheader("🔍 Filtros de búsqueda")
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            filtro_cliente = st.multiselect("Filtrar por Cliente", options=df_p["ID_CLIENTE"].unique())
        with col_f2:
            filtro_prenda = st.text_input("Buscar Prenda por nombre")

        # Aplicar lógica de filtrado
        df_filtrado = df_p.copy()
        if filtro_cliente:
            df_filtrado = df_filtrado[df_filtrado["ID_CLIENTE"].isin(filtro_cliente)]
        if filtro_prenda:
            df_filtrado = df_filtrado[df_filtrado["NOMBRE ARTÍCULO"].str.contains(filtro_prenda, case=False, na=False)]

        st.divider()
        
        # --- EDITOR DE DATOS ---
        st.info("💡 Puedes editar directamente en la tabla. Si aplicas filtros, asegúrate de quitarlos antes de añadir filas nuevas para ver todo el listado.")
        
        df_editado = st.data_editor(
            df_filtrado, 
            num_rows="dynamic", 
            use_container_width=True,
            key="editor_precios"
        )
        
        # --- GUARDAR CAMBIOS ---
        if st.button("💾 Guardar Cambios en el ODS"):
            # IMPORTANTE: Si hemos filtrado, debemos combinar los cambios con el original
            # para no perder las filas que están ocultas.
            if filtro_cliente or filtro_prenda:
                df_p.update(df_editado) # Actualiza las filas editadas
                # Si se añadieron filas nuevas mientras había filtro, las concatenamos
                nuevas_filas = df_editado[~df_editado.index.isin(df_p.index)]
                df_final = pd.concat([df_p, nuevas_filas])
            else:
                df_final = df_editado

            try:
                df_final.to_excel('listado_precios_clientes.ods', engine='odf', index=False)
                st.success("¡Listado actualizado correctamente!")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")
    else:
        st.error("No se encuentra el archivo 'listado_precios_clientes.ods'")