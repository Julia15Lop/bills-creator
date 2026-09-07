import os
import re
import ezodf
import pandas as pd

def clean_val(val):
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
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
        
        datos = {
            "n_factura": None,
            "fecha": None,
            "emisor": None,
            "cliente": None,
            "total_sin_iva": None,
            "total_con_iva": None
        }
        
        filename = os.path.basename(filepath)
        match_num = re.search(r'(?:factura|factu|n)\s*(\d+)', filename, re.IGNORECASE)
        if match_num:
            datos["n_factura"] = int(match_num.group(1))
            
        for r in range(nrows):
            for c in range(ncols):
                val = sheet[r, c].value
                if val is None:
                    continue
                val_str = str(val).strip().upper()
                
                if datos["n_factura"] is None and ("N.º" in val_str or "Nº" in val_str or "N.O" in val_str):
                    m = re.search(r'\d+', val_str)
                    if m:
                        datos["n_factura"] = int(m.group(0))
                    else:
                        for offset in range(1, 4):
                            if c + offset < ncols:
                                next_val = sheet[r, c+offset].value
                                if next_val is not None:
                                    m2 = re.search(r'\d+', str(next_val))
                                    if m2:
                                        datos["n_factura"] = int(m2.group(0))
                                        break
                
                if datos["fecha"] is None and "FECHA" in val_str:
                    for offset in range(1, 4):
                        if c + offset < ncols:
                            next_val = sheet[r, c+offset].value
                            if next_val is not None and len(str(next_val).strip()) > 3:
                                datos["fecha"] = str(next_val).strip()
                                break
                                
                if datos["total_sin_iva"] is None and (val_str == "SUBTOTAL" or val_str == "SUB-TOTAL" or val_str == "TOTAL BRUTO"):
                    for offset in range(1, 4):
                        if c + offset < ncols:
                            next_val = sheet[r, c+offset].value
                            if next_val is not None:
                                datos["total_sin_iva"] = clean_val(next_val)
                                break
                                
                if datos["total_con_iva"] is None and (val_str == "TOTAL FACTURA" or val_str == "TOTAL" or val_str == "IMPORTE LIQUIDO"):
                    for offset in range(1, 4):
                        if c + offset < ncols:
                            next_val = sheet[r, c+offset].value
                            if next_val is not None:
                                datos["total_con_iva"] = clean_val(next_val)
                                break

        for r_idx in [8, 9, 7]:
            if r_idx < nrows and 1 < ncols:
                val = sheet[r_idx, 1].value
                if val is not None:
                    val_s = str(val).strip()
                    if len(val_s) > 2 and not any(kw in val_s.upper() for kw in ["CALLE", "C/", "AVDA", "CIF:", "NIF:", "TELÉFONO:", "TELEFONO:", "EMAIL:", "DATOS"]):
                        datos["emisor"] = val_s.split(',')[0].strip()
                        break
                        
        for r_idx in [8, 9, 7]:
            if r_idx < nrows and 3 < ncols:
                val = sheet[r_idx, 3].value
                if val is not None:
                    val_s = str(val).strip()
                    if len(val_s) > 2 and not any(kw in val_s.upper() for kw in ["CALLE", "C/", "AVDA", "CIF:", "NIF:", "TELÉFONO:", "TELEFONO:", "EMAIL:", "FACTURAR", "DATOS"]):
                        datos["cliente"] = val_s.split(',')[0].strip()
                        break

        if not datos["emisor"] or len(datos["emisor"]) < 3:
            datos["emisor"] = "ARTURO"
        if not datos["cliente"] or len(datos["cliente"]) < 3:
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

def migrate():
    root_dir = r"C:\Users\julia\OneDrive\FACTURAS ARTU\ARTURO"
    dest_excel = r"data/registro_facturas.xlsx"
    
    print(f"Buscando archivos ODS en {root_dir}...")
    facturas_extraidas = []
    
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith(".ods"):
                path = os.path.join(root, f)
                print(f"Procesando: {f}")
                data = extract_ods_invoice_data(path)
                if data:
                    # Formatear la fecha a DD/MM/YY
                    fecha_str = data["fecha"]
                    try:
                        # Si viene como YYYY-MM-DD
                        if '-' in fecha_str:
                            dt = datetime.strptime(fecha_str, "%Y-%m-%d")
                        else:
                            # Si viene como DD/MM/YY o DD/MM/YYYY
                            parts = fecha_str.split('/')
                            if len(parts[2]) == 4:
                                dt = datetime.strptime(fecha_str, "%d/%m/%Y")
                            else:
                                dt = datetime.strptime(fecha_str, "%d/%m/%y")
                        fecha_formateada = dt.strftime("%d/%m/%y")
                    except Exception:
                        fecha_formateada = fecha_str
                        
                    facturas_extraidas.append({
                        "Nº Factura": str(data["n_factura"]) if data["n_factura"] is not None else "",
                        "Fecha": fecha_formateada,
                        "Emisor": str(data["emisor"]).upper(),
                        "Cliente": str(data["cliente"]).upper(),
                        "Total sin IVA": data["total_sin_iva"] if data["total_sin_iva"] is not None else 0.0,
                        "Total con IVA": data["total_con_iva"] if data["total_con_iva"] is not None else 0.0,
                        "Ruta Archivo": f
                    })
                    
    print(f"Se han extraído {len(facturas_extraidas)} facturas antiguas.")
    
    df_nuevas = pd.DataFrame(facturas_extraidas)
    
    if os.path.exists(dest_excel):
        try:
            df_existente = pd.read_excel(dest_excel)
            df_existente['Nº Factura'] = df_existente['Nº Factura'].astype(str)
            df_nuevas['Nº Factura'] = df_nuevas['Nº Factura'].astype(str)
            # Combinar y quitar duplicados basándose en el Nº de Factura y el Cliente
            df_final = pd.concat([df_existente, df_nuevas], ignore_index=True)
            df_final = df_final.drop_duplicates(subset=["Nº Factura", "Cliente"], keep="first")
        except Exception as e:
            print(f"Error al leer el excel existente: {e}")
            df_final = df_nuevas
    else:
        df_final = df_nuevas
        
    # Guardar en Excel
    os.makedirs(os.path.dirname(dest_excel), exist_ok=True)
    df_final.to_excel(dest_excel, engine='openpyxl', index=False)
    print(f"¡Migración completada con éxito! Se guardó en {dest_excel} con un total de {len(df_final)} registros.")

if __name__ == "__main__":
    migrate()
