import os
import re
import ezodf
import pandas as pd

def clean_val(val):
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    # Si es un string, limpiar formato euro
    s = str(val).replace('€', '').replace(' ', '').replace(',', '.').strip()
    try:
        return float(s)
    except:
        return 0.0

def extract_ods_invoice_data(filepath):
    try:
        ods = ezodf.opendoc(filepath)
        sheet = ods.sheets[0]
        nrows = sheet.nrows()
        ncols = sheet.ncols()
        
        # Buscar valores mediante escaneo completo para mayor robustez
        datos = {
            "n_factura": None,
            "fecha": None,
            "emisor": None,
            "cliente": None,
            "total_sin_iva": None,
            "total_con_iva": None
        }
        
        # 1. Intentar obtener número de factura por nombre de archivo
        filename = os.path.basename(filepath)
        match_num = re.search(r'(?:factura|factu|n)\s*(\d+)', filename, re.IGNORECASE)
        if match_num:
            datos["n_factura"] = int(match_num.group(1))
            
        # 2. Escanear todas las celdas
        for r in range(nrows):
            for c in range(ncols):
                val = sheet[r, c].value
                if val is None:
                    continue
                val_str = str(val).strip().upper()
                
                # Buscar Número de Factura si no se obtuvo por nombre
                if datos["n_factura"] is None and ("N.º" in val_str or "Nº" in val_str or "N.O" in val_str):
                    # Si tiene el número en la misma celda (ej: "N.º 209")
                    m = re.search(r'\d+', val_str)
                    if m:
                        datos["n_factura"] = int(m.group(0))
                    else:
                        # Buscar en la celda de la derecha
                        for offset in range(1, 4):
                            if c + offset < ncols:
                                next_val = sheet[r, c+offset].value
                                if next_val is not None:
                                    m2 = re.search(r'\d+', str(next_val))
                                    if m2:
                                        datos["n_factura"] = int(m2.group(0))
                                        break
                
                # Buscar Fecha
                if datos["fecha"] is None and "FECHA" in val_str:
                    # Buscar en la celda de la derecha o subsiguiente
                    for offset in range(1, 4):
                        if c + offset < ncols:
                            next_val = sheet[r, c+offset].value
                            if next_val is not None and len(str(next_val).strip()) > 3:
                                datos["fecha"] = str(next_val).strip()
                                break
                                
                # Buscar Subtotal (Total sin IVA)
                if datos["total_sin_iva"] is None and (val_str == "SUBTOTAL" or val_str == "SUB-TOTAL" or val_str == "TOTAL BRUTO"):
                    for offset in range(1, 4):
                        if c + offset < ncols:
                            next_val = sheet[r, c+offset].value
                            if next_val is not None:
                                datos["total_sin_iva"] = clean_val(next_val)
                                break
                                
                # Buscar Total con IVA
                if datos["total_con_iva"] is None and (val_str == "TOTAL FACTURA" or val_str == "TOTAL" or val_str == "IMPORTE LIQUIDO"):
                    for offset in range(1, 4):
                        if c + offset < ncols:
                            next_val = sheet[r, c+offset].value
                            if next_val is not None:
                                datos["total_con_iva"] = clean_val(next_val)
                                break

        # 3. Intentar obtener Emisor y Cliente de celdas específicas
        # En plantillas estándar:
        # Emisor está en Row 10 Col 2 (index 9, 1) o Row 2 Col 2 (index 1, 1)
        # Cliente está en Row 10 Col 4 (index 9, 3) o Row 9 Col 4 (index 8, 3)
        # 3. Intentar obtener Emisor y Cliente buscando en las filas 8, 9, 10
        # Emisor en columna B (index 1), Cliente en columna D (index 3)
        for r_idx in [8, 9, 7]: # Buscar en fila 9, luego 10, luego 8 (0-indexed)
            if r_idx < nrows and 1 < ncols:
                val = sheet[r_idx, 1].value
                if val is not None:
                    val_s = str(val).strip()
                    # Ignorar si parece dirección, cif, teléfono o email
                    if len(val_s) > 2 and not any(kw in val_s.upper() for kw in ["CALLE", "C/", "AVDA", "CIF:", "NIF:", "TELÉFONO:", "TELEFONO:", "EMAIL:", "DATOS"]):
                        datos["emisor"] = val_s.split(',')[0].strip()
                        break
                        
        for r_idx in [8, 9, 7]: # Buscar en fila 9, luego 10, luego 8 (0-indexed)
            if r_idx < nrows and 3 < ncols:
                val = sheet[r_idx, 3].value
                if val is not None:
                    val_s = str(val).strip()
                    # Ignorar si parece dirección, cif o datos de cabecera
                    if len(val_s) > 2 and not any(kw in val_s.upper() for kw in ["CALLE", "C/", "AVDA", "CIF:", "NIF:", "TELÉFONO:", "TELEFONO:", "EMAIL:", "FACTURAR", "DATOS"]):
                        datos["cliente"] = val_s.split(',')[0].strip()
                        break

        # Fallbacks si no se encontraron en celdas
        if not datos["emisor"] or len(datos["emisor"]) < 3:
            datos["emisor"] = "ARTURO" # Ya que está en la carpeta de ARTURO
        if not datos["cliente"] or len(datos["cliente"]) < 3:
            # Deducir por nombre de archivo
            if "belinda" in filename.lower():
                datos["cliente"] = "BELINDA"
            elif "woven" in filename.lower():
                datos["cliente"] = "WOVEN"
            else:
                datos["cliente"] = "DESCONOCIDO"

        return datos
    except Exception as e:
        print(f"Error procesando {filepath}: {e}")
        return None

# Probar la extracción en un par de archivos
root_dir = r"C:\Users\julia\OneDrive\FACTURAS ARTU\ARTURO"
for root, dirs, files in os.walk(root_dir):
    for f in files:
        if f.lower().endswith(".ods"):
            path = os.path.join(root, f)
            data = extract_ods_invoice_data(path)
            print(f"File: {f} -> Extracted: {data}")
