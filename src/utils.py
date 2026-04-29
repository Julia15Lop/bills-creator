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