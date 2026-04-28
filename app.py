import streamlit as st
import pandas as pd

st.title("📦 Gestión de Pedido por Tallas")

# 1. Definimos las tallas que manejas habitualmente
lista_tallas = ["T-36", "T-38", "T-40", "T-42", "T-44", "T-46"]

# 2. Creamos un DataFrame vacío para la entrada de datos
if 'df_pedido' not in st.session_state:
    # Columnas: Prenda + todas las tallas
    columnas = ["Nombre Prenda"] + lista_tallas
    st.session_state.df_pedido = pd.DataFrame(columns=columnas)

st.subheader("Introduce las unidades por prenda y talla:")

# 3. El Editor de Datos Mágico
# 'num_rows="dynamic"' permite al usuario añadir nuevas prendas (filas)
pedido_editado = st.data_editor(
    st.session_state.df_pedido, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "Nombre Prenda": st.column_config.TextColumn("Prenda", help="Nombre del modelo", width="medium"),
        # Configuramos las tallas para que solo acepten números positivos
        **{t: st.column_config.NumberColumn(t, min_value=0, format="%d") for t in lista_tallas}
    }
)

if st.button("🚀 Procesar Factura con estos datos"):
    # Aquí transformamos esa tabla plana al formato JSON que necesita tu mcp_facturacion.py
    resultado_json = {}
    
    for _, fila in pedido_editado.iterrows():
        nombre = fila["Nombre Prenda"]
        if pd.isna(nombre) or nombre == "": continue
        
        tallas_prenda = {}
        for t in lista_tallas:
            cantidad = fila[t]
            if cantidad > 0:
                tallas_prenda[t] = int(cantidad)
        
        if tallas_prenda:
            resultado_json[nombre] = tallas_prenda

    st.write("Datos listos para enviar al motor:")
    st.json(resultado_json)