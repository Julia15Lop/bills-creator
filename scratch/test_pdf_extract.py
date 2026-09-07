import os
import re
import pypdf

def clean_pdf_val(val_str):
    # Reemplazar puntos de miles por nada, y comas decimales por puntos
    s = val_str.replace('.', '').replace(',', '.').replace('€', '').replace('', '').strip()
    try:
        return float(s)
    except:
        return 0.0

def extract_pdf_invoice_data(filepath):
    try:
        reader = pypdf.PdfReader(filepath)
        text = reader.pages[0].extract_text()
        
        datos = {
            "n_factura": None,
            "fecha": None,
            "emisor": None,
            "cliente": None,
            "total_sin_iva": None,
            "total_con_iva": None
        }
        
        # 1. Número de Factura
        match_num = re.search(r'(?:N\.[º°oO\s]*|N[º°oO\s]+)\s*(\d+)', text, re.IGNORECASE)
        if match_num:
            datos["n_factura"] = int(match_num.group(1))
        else:
            filename = os.path.basename(filepath)
            m = re.search(r'\d+', filename)
            if m:
                datos["n_factura"] = int(m.group(0))
                
        # 2. Fecha
        match_fecha = re.search(r'FECHA:\s*([\d/.-]+)', text, re.IGNORECASE)
        if match_fecha:
            datos["fecha"] = match_fecha.group(1).strip()
            
        # 3. Totales
        # Buscar Subtotal
        match_sub = re.search(r'(?:SUB-TOTAL|SUBTOTAL|TOTAL BRUTO)[^\d\n]*([\d.,]+)', text, re.IGNORECASE)
        if match_sub:
            datos["total_sin_iva"] = clean_pdf_val(match_sub.group(1))
            
        # Buscar Total
        match_tot = re.search(r'(?:TOTAL FACTURA|TOTAL|IMPORTE LIQUIDO)[^\d\n]*([\d.,]+)', text, re.IGNORECASE)
        if match_tot:
            datos["total_con_iva"] = clean_pdf_val(match_tot.group(1))
            
        # 4. Emisor y Cliente
        # Buscamos en el texto
        text_upper = text.upper()
        
        # Identificar Cliente
        if "BELINDA" in text_upper:
            datos["cliente"] = "BELINDA"
        elif "WOVEN" in text_upper:
            datos["cliente"] = "WOVEN"
        elif "JULIA L" in text_upper or "JULIA LOPEZ" in text_upper:
            datos["cliente"] = "JULIA LOPEZ"
        else:
            datos["cliente"] = "DESCONOCIDO"
            
        # Identificar Emisor
        if "ARTURO CASTRO" in text_upper or "ARTURO" in text_upper:
            datos["emisor"] = "ARTURO"
        elif "ARTU PATRONES" in text_upper:
            datos["emisor"] = "ARTURO"
        else:
            datos["emisor"] = "ARTURO"
            
        return datos
    except Exception as e:
        print(f"Error procesando PDF {filepath}: {e}")
        return None

# Test on all PDF files
root_dir = r"C:\Users\julia\OneDrive\FACTURAS ARTU\ARTURO"
for root, dirs, files in os.walk(root_dir):
    for f in files:
        if f.lower().endswith(".pdf"):
            path = os.path.join(root, f)
            data = extract_pdf_invoice_data(path)
            print(f"PDF: {f} -> Extracted: {data}")
