"""
Script de migración de facturas históricas a data/registro_facturas.xlsx
Lee todos los archivos PDF de la carpeta de facturas, extrae los datos clave
y los consolida en el Excel del historial de la aplicación.

Uso:
    python tools/import_history.py [ruta_carpeta_facturas]

Si no se proporciona ruta, se usa la ruta por defecto del proyecto.
"""

import os
import re
import sys
import pypdf
import pandas as pd
from datetime import datetime


def clean_pdf_amount(val_str):
    """Convierte string de importe (ej: '3.267,00 €') a float."""
    if not val_str:
        return 0.0
    # Eliminar símbolo de euro y espacios
    s = val_str.strip().replace('€', '').replace(' ', '').replace('\xa0', '')
    # Formato español: punto separador de miles, coma decimal → '3.267,00' → 3267.00
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0


MESES_ES = {
    'ENE': 1, 'ENERO': 1, 'JAN': 1,
    'FEB': 2, 'FEBRERO': 2,
    'MAR': 3, 'MARZO': 3,
    'ABR': 4, 'ABRIL': 4, 'APR': 4,
    'MAY': 5, 'MAYO': 5,
    'JUN': 6, 'JUNIO': 6,
    'JUL': 7, 'JULIO': 7,
    'AGO': 8, 'AGOSTO': 8, 'AUG': 8,
    'SEP': 9, 'SEPT': 9, 'SEPTIEMBRE': 9,
    'OCT': 10, 'OCTUBRE': 10,
    'NOV': 11, 'NOVIEMBRE': 11,
    'DIC': 12, 'DICIEMBRE': 12, 'DEC': 12,
}


def inferir_fecha_desde_ruta(filepath):
    """Intenta obtener año y mes del path de carpeta. Devuelve (año, mes) o (None, None)."""
    parts = filepath.replace('\\', '/').upper().split('/')
    año = None
    mes = None
    for part in reversed(parts):
        # Año: "2025", "2026", "NOV 25", "DIC 25", "ENERO 2026"
        m_año = re.search(r'20(\d{2})', part)
        if m_año:
            año = int('20' + m_año.group(1))
        elif re.search(r'\b(\d{2})\b', part):
            m2 = re.search(r'\b(\d{2})\b', part)
            y = int(m2.group(1))
            if 20 <= y <= 30:
                año = 2000 + y
        # Mes: buscar nombre de mes en español o abreviatura
        for nombre, num in MESES_ES.items():
            if nombre in part:
                mes = num
                break
        if año and mes:
            break
    return año, mes


def extract_pdf_invoice_data(filepath):
    """Extrae datos de una factura en PDF."""
    try:
        reader = pypdf.PdfReader(filepath)
        # Leer todas las páginas y unir el texto
        text = '\n'.join(page.extract_text() or '' for page in reader.pages)

        datos = {
            "n_factura": None,
            "fecha": None,
            "emisor": "ARTURO CASTRO",
            "cliente": None,
            "total_sin_iva": 0.0,
            "total_con_iva": 0.0
        }

        filename = os.path.basename(filepath)

        # --- Número de factura ---
        # Patrones: "N.º 207", "N.° 207", "N.o 207"
        match_num = re.search(r'N\s*[.·]?\s*[º°oO]\s*(\d+)', text, re.IGNORECASE)
        if match_num:
            datos["n_factura"] = int(match_num.group(1))
        else:
            # Desde el nombre de archivo: "FACTURA 207.pdf", "FACTURA - 178.pdf"
            m = re.search(r'(\d{3,})', filename)
            if m:
                datos["n_factura"] = int(m.group(1))

        # --- Fecha ---
        match_fecha = re.search(r'FECHA\s*:\s*([\d]{1,2}[/.-][\d]{1,2}[/.-][\d]{2,4})', text, re.IGNORECASE)
        if match_fecha:
            datos["fecha"] = match_fecha.group(1).strip()
        else:
            # Si no hay fecha en el PDF, intentar construirla desde el año de la carpeta
            año_ruta, mes_ruta = inferir_fecha_desde_ruta(filepath)
            if año_ruta:
                mes_str = str(mes_ruta or 1).zfill(2)
                año_str = str(año_ruta)[-2:]
                datos["fecha"] = f"01/{mes_str}/{año_str}"

        # --- Totales (buscar en todas las páginas) ---
        # SUB-TOTAL: "SUB-TOTAL   3.267,00 €" o "SUBTOTAL   2.515,00"
        match_sub = re.search(
            r'(?:SUB-?TOTAL|SUBTOTAL|TOTAL BRUTO)\s+([\d.,]+)',
            text, re.IGNORECASE
        )
        if match_sub:
            datos["total_sin_iva"] = clean_pdf_amount(match_sub.group(1))

        # TOTAL FACTURA: buscar la última ocurrencia para evitar confusión con totales parciales
        matches_tot = list(re.finditer(
            r'TOTAL FACTURA\s+([\d.,]+)',
            text, re.IGNORECASE
        ))
        if matches_tot:
            datos["total_con_iva"] = clean_pdf_amount(matches_tot[-1].group(1))
        else:
            # Si no hay "TOTAL FACTURA", buscar "IMPORTE LIQUIDO"
            match_liq = re.search(r'IMPORTE LI[QK]UIDO\s+([\d.,]+)', text, re.IGNORECASE)
            if match_liq:
                datos["total_con_iva"] = clean_pdf_amount(match_liq.group(1))

        # --- Cliente ---
        text_up = text.upper()
        if "BELINDA" in text_up:
            datos["cliente"] = "BELINDA WINGS"
        elif "WOVEN" in text_up:
            datos["cliente"] = "WOVEN LABEL"
        elif "JULIA" in text_up:
            datos["cliente"] = "JULIA LOPEZ"
        else:
            datos["cliente"] = "DESCONOCIDO"

        return datos

    except Exception as e:
        print(f"  [ERROR] No se pudo procesar {os.path.basename(filepath)}: {e}")
        return None


def parse_fecha(fecha_str):
    """Convierte una cadena de fecha a objeto datetime, tolerante a distintos formatos."""
    if not fecha_str:
        return None
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%y", "%d-%m-%Y"):
        try:
            return datetime.strptime(fecha_str.strip(), fmt)
        except:
            pass
    return None


def migrate(root_dir, dest_excel='data/registro_facturas.xlsx'):
    """
    Escanea recursivamente root_dir buscando PDFs de facturas,
    extrae los datos y los guarda en dest_excel.
    """
    print(f"\n{'='*60}")
    print(f"  IMPORTACIÓN DE FACTURAS HISTÓRICAS")
    print(f"  Carpeta fuente: {root_dir}")
    print(f"  Destino: {dest_excel}")
    print(f"{'='*60}\n")

    if not os.path.isdir(root_dir):
        print(f"[ERROR] La carpeta '{root_dir}' no existe.")
        return

    facturas_extraidas = []
    vistos = {}  # Para desduplicar: clave = (n_factura, cliente)

    for root, dirs, files in os.walk(root_dir):
        # Ordenar archivos para que si hay duplicados, se quede el nombre más descriptivo
        pdf_files = sorted([f for f in files if f.lower().endswith('.pdf')])
        for f in pdf_files:
            # Ignorar PDFs multi-factura genéricos (e.g. "Facturas Diciembre 178-181.pdf")
            if re.search(r'\d+[-–]\d+', f):
                print(f"  [OMITIDO] {f}  (archivo agrupado)")
                continue

            path = os.path.join(root, f)
            print(f"  Procesando: {f}")
            data = extract_pdf_invoice_data(path)
            if not data:
                continue

            # Parsear y formatear fecha
            dt = parse_fecha(data["fecha"])
            if dt:
                fecha_fmt = dt.strftime("%d/%m/%y")
                año = dt.year
                mes = dt.month
            else:
                fecha_fmt = data["fecha"] or "?"
                año_ruta, mes_ruta = inferir_fecha_desde_ruta(path)
                año = año_ruta or 2025
                mes = mes_ruta or 1

            # Desduplicar: si ya vimos esta factura con igual nº y cliente, saltamos
            clave = (data["n_factura"], data["cliente"])
            if clave in vistos:
                print(f"    → Duplicado de nº {data['n_factura']} ({data['cliente']}), omitido.")
                continue
            vistos[clave] = True

            facturas_extraidas.append({
                "Nº Factura": str(data["n_factura"]) if data["n_factura"] else "",
                "Fecha": fecha_fmt,
                "Año": año,
                "Mes": mes,
                "Emisor": data["emisor"].upper(),
                "Cliente": data["cliente"].upper(),
                "Total sin IVA": data["total_sin_iva"],
                "Total con IVA": data["total_con_iva"],
                "Ruta Archivo": f
            })
            print(f"    OK N {data['n_factura']} | {fecha_fmt} | {data['cliente']} | Sin IVA: {data['total_sin_iva']} | Con IVA: {data['total_con_iva']}")

    print(f"\n  Total facturas procesadas: {len(facturas_extraidas)}")

    df_nuevas = pd.DataFrame(facturas_extraidas)

    # Si ya existe el Excel, combinar sin duplicar
    if os.path.exists(dest_excel):
        try:
            df_existente = pd.read_excel(dest_excel)
            df_existente['Nº Factura'] = df_existente['Nº Factura'].astype(str)
            df_nuevas['Nº Factura'] = df_nuevas['Nº Factura'].astype(str)
            df_final = pd.concat([df_existente, df_nuevas], ignore_index=True)
            df_final = df_final.drop_duplicates(subset=["Nº Factura", "Cliente"], keep="last")
        except Exception as e:
            print(f"  [AVISO] No se pudo leer el Excel existente ({e}). Se creará uno nuevo.")
            df_final = df_nuevas
    else:
        df_final = df_nuevas

    # Ordenar por año y número de factura
    try:
        df_final['Nº Factura_int'] = pd.to_numeric(df_final['Nº Factura'], errors='coerce')
        df_final = df_final.sort_values(by=['Año', 'Mes', 'Nº Factura_int']).drop(columns=['Nº Factura_int'], errors='ignore')
    except:
        pass

    os.makedirs(os.path.dirname(dest_excel) if os.path.dirname(dest_excel) else '.', exist_ok=True)
    df_final.to_excel(dest_excel, engine='openpyxl', index=False)

    print(f"\n{'='*60}")
    print(f"  MIGRACION COMPLETADA!")
    print(f"  Total registros en el Excel: {len(df_final)}")
    print(f"  Guardado en: {os.path.abspath(dest_excel)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Acepta ruta como argumento de línea de comandos
    if len(sys.argv) >= 2:
        carpeta = sys.argv[1]
    else:
        # Ruta por defecto (solo para uso local de la propietaria)
        carpeta = r"C:\Users\julia\OneDrive\FACTURAS ARTU\ARTURO"

    dest = sys.argv[2] if len(sys.argv) >= 3 else 'data/registro_facturas.xlsx'
    migrate(carpeta, dest)
