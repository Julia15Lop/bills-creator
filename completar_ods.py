import json
import ezodf
import os
from datetime import datetime

def generar():
    try:
        if not os.path.exists('ultimo_resultado.json'): return
        with open('ultimo_resultado.json', 'r', encoding='utf-8') as f: res = json.load(f)
        
        ods = ezodf.opendoc(f"plantilla_{res['cliente']}.ods")
        sheet = ods.sheets[0]
        emi = res['emisor']

        # Datos Arturo/Carmen
        sheet['B10'].set_value(emi['nombre_fiscal'])
        sheet['B11'].set_value(f"CIF: {emi['cif']}")
        sheet['B12'].set_value(emi['direccion'])
        sheet['B13'].set_value(emi['codigo_postal'])
        sheet['B14'].set_value(f"Teléfono: {emi['telefono']}")
        sheet['B15'].set_value(f"Email: {emi['mail']}")

        # Encabezado
        sheet['E3'].set_value(f"N.º {res['factura']}")
        sheet['G5'].set_value(res['fecha']) # Fecha en formato texto DD/MM/YYYY

        # Líneas
        for i, item in enumerate(res['items']):
            f = 19 + i
            sheet[f'B{f}'].set_value(item['desc'])
            sheet[f'C{f}'].set_value(item['talla'])
            sheet[f'E{f}'].set_value(item['cant'])
            sheet[f'F{f}'].set_value(item['precio'])

        # Pago
        sheet['B43'].set_value(f"BANCO: {emi['cuenta']}")
        sheet['B44'].set_value(f"IBAN: {emi['numero_cuenta']}")

        # Nombre único para no sobreescribir mientras está abierto
        h = datetime.now().strftime("%H%M%S")
        ods.saveas(f"Factura_{res['factura']}_{res['cliente']}_{h}.ods")
        
    except Exception as e:
        with open('error_ods.txt', 'w') as log: log.write(str(e))

if __name__ == "__main__":
    generar()