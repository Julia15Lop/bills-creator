import ezodf
import os
from datetime import datetime

def generar_ods(res):
    # 1. Asegurar que la carpeta output existe (Mentalidad SRE)
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    plantilla = f"templates/plantilla_{res['cliente']}.ods"
    ods = ezodf.opendoc(plantilla)
    sheet = ods.sheets[0]
    emi = res['emisor']

    # --- DATOS DEL EMISOR ---
    sheet['B10'].set_value(emi['nombre_fiscal'])
    sheet['B11'].set_value(f"CIF: {emi['cif']}")
    sheet['B12'].set_value(emi['direccion'])
    sheet['B13'].set_value(emi['codigo_postal'])
    sheet['B14'].set_value(f"Teléfono: {emi['telefono']}")
    sheet['B15'].set_value(f"Email: {emi['mail']}")

    # --- ENCABEZADO ---
    sheet['E3'].set_value(f"N.º {res['factura']}")
    
    # EL TRUCO PARA LA FECHA: 
    # Forzamos el valor como string puro y duro para que el ODS no lo formatee.
    celda_fecha = sheet['G5']
    str(f"DEBUG: Fecha detectada como: **{res['fecha']}**")
    celda_fecha.set_value(str(res['fecha'])) 

    # --- ÍTEMS Y CÁLCULOS FORZADOS ---
    for i, item in enumerate(res['items']):
        fila_idx = 19 + i
        sheet[f'B{fila_idx}'].set_value(item['desc'])
        sheet[f'C{fila_idx}'].set_value(item['talla'])
        sheet[f'E{fila_idx}'].set_value(item['cant'])
        sheet[f'F{fila_idx}'].set_value(item['precio'])
        # Escribimos el valor calculado por Python para evitar fallos de fórmula
        sheet[f'G{fila_idx}'].set_value(item['subtotal']) 

    # --- DATOS DE PAGO ---
    sheet['B43'].set_value(f"BANCO: {emi['cuenta']}")
    sheet['B44'].set_value(f"IBAN: {emi['numero_cuenta']}")

    # --- GUARDADO EN CARPETA OUTPUT ---
    timestamp = datetime.now().strftime('%H%M%S')
    nombre_archivo = f"Factura_{res['factura']}_{res['cliente']}_{timestamp}.ods"
    ruta_final = os.path.join(output_dir, nombre_archivo)
    
    ods.saveas(ruta_final)
    return ruta_final # Devolvemos la ruta completa para que app.py la encuentre