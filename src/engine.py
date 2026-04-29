import re
import pandas as pd
from .utils import limpiar_precio 

def procesar_factura(emisor_name, cliente, fecha, objetivo, prendas_pedido, df_precios, emisor_data):
    """
    Calcula los totales y prepara los datos para el generador de ODS.
    """
    # Usamos el número que viene del JSON y le sumamos 1
    nuevo_num = emisor_data['ultimo_numero'] + 1
    
    items_finales = []
    total_base = 0

    for modelo, tallas in prendas_pedido.items():
        # Buscamos precio filtrando por modelo y cliente
        mask = (df_precios['NOMBRE ARTÍCULO'].str.contains(re.escape(modelo), case=False, na=False)) & \
               (df_precios['ID_CLIENTE'].str.contains(cliente, case=False, na=False))
        fila = df_precios[mask]
        
        if not fila.empty:
            p_unit = limpiar_precio(fila.iloc[0]['PRECIO CLIENTE'])
            
            for t, cant in tallas.items():
                # Solo procesamos si hay cantidad real
                if cant > 0:
                    subtotal = round(p_unit * cant, 2)
                    total_base += subtotal
                    items_finales.append({
                        "desc": fila.iloc[0]['NOMBRE ARTÍCULO'],
                        "talla": t,
                        "cant": cant,
                        "precio": p_unit,
                        "subtotal": subtotal 
                    })

    # Cálculo de IVA (21%)
    total_iva = round(total_base * 1.21, 2)
    
    return {
        "factura": nuevo_num,
        "emisor": emisor_data, 
        "cliente": cliente,
        "fecha": fecha,
        "items": items_finales,
        "total_estimado": total_iva,
        "supera_objetivo": total_iva > objetivo
    }