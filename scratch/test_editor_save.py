import streamlit as st
import pandas as pd
import os

st.title("Test Prices View Editor")

PATH_PRECIOS = 'data/listado_precios_clientes.xlsx'

if not os.path.exists(PATH_PRECIOS):
    st.error(f"No file {PATH_PRECIOS}")
else:
    df_precios = pd.read_excel(PATH_PRECIOS)
    
    # Let's filter by a client
    clientes = ["Todos"] + sorted(list(df_precios['ID_CLIENTE'].unique()))
    cliente_sel = st.selectbox("Cliente:", clientes)
    
    df_mostrar = df_precios.copy()
    if cliente_sel != "Todos":
        df_mostrar = df_mostrar[df_mostrar['ID_CLIENTE'] == cliente_sel]
        
    st.write(f"df_mostrar shape: {df_mostrar.shape}")
    
    df_editado = st.data_editor(df_mostrar, key="test_editor", num_rows="dynamic")
    
    if st.button("💾 Guardar Cambios"):
        st.write("--- GUARDANDO ---")
        st.write("df_editado:")
        st.write(df_editado.head(5))
        
        # Test update
        df_copy = df_precios.copy()
        df_copy.update(df_editado)
        
        st.write("df_copy updated (head 5):")
        st.write(df_copy.head(5))
        
        # Check if the change actually took place in df_copy
        # We can compare df_copy and df_precios
        diff = df_copy != df_precios
        # Since NaN != NaN, we fillna or look at actual changes
        diff_mask = (df_copy != df_precios) & ~(df_copy.isna() & df_precios.isna())
        changed_rows = df_copy[diff_mask.any(axis=1)]
        st.write("Filas cambiadas detectadas:")
        st.write(changed_rows)
        
        if not changed_rows.empty:
            df_copy.to_excel(PATH_PRECIOS, engine='openpyxl', index=False)
            st.success("Guardado en archivo de Excel!")
        else:
            st.warning("No se detectó ningún cambio para guardar en df_copy.")
