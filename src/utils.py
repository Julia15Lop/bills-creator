import re
import pandas as pd

def limpiar_precio(valor):
    """Convierte cualquier formato de precio (25,50 €, 1.200, 25.5) a float puro."""
    if pd.isna(valor) or valor is None: 
        return 0.0
    
    # Eliminar símbolo de euro y espacios
    s = str(valor).replace('€', '').replace(' ', '').strip()
    
    # Manejar formato europeo (1.200,50) -> (1200.50)
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
        
    try:
        # Extraer solo números y el punto decimal
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except:
        return 0.0

def limpiar_nombre_archivo(texto):
    """Evita caracteres raros en el nombre del archivo final."""
    return re.sub(r'[^\w\s-]', '', texto).strip().replace(' ', '_')

def registrar_factura(n_factura, fecha, emisor, cliente, total_sin_iva, total_con_iva, ruta_archivo, path_registro='data/registro_facturas.xlsx'):
    import os
    nuevo_registro = {
        "Nº Factura": [n_factura],
        "Fecha": [fecha],
        "Emisor": [emisor],
        "Cliente": [cliente],
        "Total sin IVA": [total_sin_iva],
        "Total con IVA": [total_con_iva],
        "Ruta Archivo": [ruta_archivo]
    }
    df_nuevo = pd.DataFrame(nuevo_registro)
    
    if os.path.exists(path_registro):
        try:
            df_existente = pd.read_excel(path_registro)
            df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
        except Exception:
            df_final = df_nuevo
    else:
        df_final = df_nuevo
        
    df_final.to_excel(path_registro, engine='openpyxl', index=False)