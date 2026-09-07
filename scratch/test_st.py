import streamlit as st
import pandas as pd

st.title("Test Data Editor")

df = pd.DataFrame({"A": [1, 2, 3], "B": ["a", "b", "c"]})

df_editado = st.data_editor(df, key="editor")

if st.button("Guardar"):
    st.write("df_editado:")
    st.write(df_editado)
    st.write("session_state['editor']:")
    st.write(st.session_state["editor"])
