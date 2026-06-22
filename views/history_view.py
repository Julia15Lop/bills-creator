import streamlit as st
import pandas as pd
import os
from datetime import datetime

def render_history_view():
    PATH_REGISTRO = 'data/registro_facturas.xlsx'
    st.subheader("📊 Historial de Facturas y Cobros")

    if not os.path.exists(PATH_REGISTRO):
        st.info("ℹ️ Aún no se ha registrado ninguna factura. Las facturas nuevas que generes se guardarán aquí automáticamente.")
        return

    try:
        df_historial = pd.read_excel(PATH_REGISTRO)
    except Exception as e:
        st.error(f"Error al leer el historial: {e}")
        return

    if df_historial.empty:
        st.info("ℹ️ El registro de facturas está vacío.")
        return

    # Asegurarnos de que el formato de las columnas sea correcto
    df_historial['Nº Factura'] = df_historial['Nº Factura'].astype(str)
    
    # Procesar fechas para filtros
    df_mostrar = df_historial.copy()
    try:
        # Convertir a datetime para poder ordenar y agrupar por mes
        df_mostrar['Fecha_dt'] = pd.to_datetime(df_mostrar['Fecha'], format='%d/%m/%y', errors='coerce')
        # Si hay valores nulos en fecha, rellenar con hoy
        df_mostrar['Fecha_dt'] = df_mostrar['Fecha_dt'].fillna(pd.Timestamp.now())
        df_mostrar = df_mostrar.sort_values(by='Fecha_dt', ascending=False)
    except Exception:
        df_mostrar['Fecha_dt'] = pd.Timestamp.now()

    # --- FILTROS DE CONSULTA ---
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        # Mapeo de meses en español
        meses_es = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
            7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        
        df_mostrar['Mes_Año_Str'] = df_mostrar['Fecha_dt'].apply(lambda x: f"{meses_es.get(x.month, '')} {x.year}")
        # Obtener los meses ordenados cronológicamente descendente
        meses_unicos = df_mostrar.sort_values(by='Fecha_dt', ascending=False)['Mes_Año_Str'].unique().tolist()
        opciones_mes = ["Todos"] + meses_unicos
        
        mes_sel = st.selectbox("📅 Filtrar por Mes:", opciones_mes)

    with col_f2:
        # Filtrar por Cliente
        clientes_disp = ["Todos"] + sorted(list(df_historial['Cliente'].dropna().unique()))
        cliente_sel = st.selectbox("🎯 Filtrar por Cliente:", clientes_disp)

    with col_f3:
        # Filtrar por Emisor
        emisores_disp = ["Todos"] + sorted(list(df_historial['Emisor'].dropna().unique()))
        emisor_sel = st.selectbox("👤 Filtrar por Emisor:", emisores_disp)

    # Aplicar Filtros
    if mes_sel != "Todos":
        df_mostrar = df_mostrar[df_mostrar['Mes_Año_Str'] == mes_sel]
    if cliente_sel != "Todos":
        df_mostrar = df_mostrar[df_mostrar['Cliente'] == cliente_sel]
    if emisor_sel != "Todos":
        df_mostrar = df_mostrar[df_mostrar['Emisor'] == emisor_sel]

    # --- MÉTRICAS ---
    total_sin_iva = df_mostrar['Total sin IVA'].sum()
    total_con_iva = df_mostrar['Total con IVA'].sum()
    iva_acumulado = total_con_iva - total_sin_iva
    cant_facturas = len(df_mostrar)

    st.write("### 📈 Resumen Financiero (Selección)")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Total Facturado (Sin IVA)", f"{total_sin_iva:,.2f} €")
    with col_m2:
        st.metric("IVA Acumulado (21%)", f"{iva_acumulado:,.2f} €")
    with col_m3:
        st.metric("Total Cobrado (Con IVA)", f"{total_con_iva:,.2f} €")
    with col_m4:
        st.metric("Facturas Emitidas", f"{cant_facturas}")

    st.divider()

    # --- TABLA DE REGISTROS ---
    st.write("### 📋 Registro Detallado")
    
    # Preparar el dataframe para mostrar
    columnas_mostrar = ["Nº Factura", "Fecha", "Emisor", "Cliente", "Total sin IVA", "Total con IVA", "Ruta Archivo"]
    df_editor = df_mostrar[columnas_mostrar].copy()

    df_editado = st.data_editor(
        df_editor,
        use_container_width=True,
        num_rows="dynamic",
        key="editor_historial_facturas"
    )

    # --- BOTONES ---
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Guardar Cambios en Historial", type="primary", use_container_width=True):
            try:
                # Al igual que en prices_view, actualizamos df_historial con df_editado por coincidencia de índice
                df_historial.update(df_editado)
                
                # Si hay nuevas filas agregadas dinámicamente
                if len(df_editado) > len(df_editor):
                    nuevas = df_editado.iloc[len(df_editor):]
                    df_historial = pd.concat([df_historial, nuevas], ignore_index=True)
                
                df_historial.to_excel(PATH_REGISTRO, engine='openpyxl', index=False)
                st.success("✅ Cambios guardados con éxito en el historial.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    with c2:
        # Exportar datos a CSV
        csv = df_editor.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📥 Exportar Selección a Excel/CSV",
            data=csv,
            file_name=f"historial_facturas_{mes_sel.replace(' ', '_') if mes_sel != 'Todos' else 'completo'}.csv",
            mime="text/csv",
            use_container_width=True
        )
