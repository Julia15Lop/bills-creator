import json
import ezodf
import os

def generar():
    try:
        with open('ultimo_resultado.json', 'r', encoding='utf-8') as f:
            res = json.load(f)
        
        plantilla = f"plantilla_{res['cliente']}.ods"
        ods = ezodf.opendoc(plantilla)
        sheet = ods.sheets[0]
        emi = res['emisor']

        # Datos de contacto (B10-B15)
        sheet['B10'].set_value(emi['nombre_fiscal'])
        sheet['B11'].set_value(emi['cif'])
        sheet['B12'].set_value(emi['direccion'])
        sheet['B13'].set_value(emi['codigo_postal'])
        sheet['B14'].set_value(emi['telefono'])
        sheet['B15'].set_value(emi['mail'])

        # Encabezado (Fila 3 y 5)
        sheet['E3'].set_value(f"N.º {res['factura']}")
        sheet['G5'].set_value(res['fecha'])

        # Cuerpo (Desde fila 19) - Solo columnas B, C, E, F
        for i, item in enumerate(res['items']):
            f = 19 + i
            sheet[f'B{f}'].set_value(item['desc'])
            sheet[f'C{f}'].set_value(item['talla'])
            sheet[f'E{f}'].set_value(item['cant'])
            sheet[f'F{f}'].set_value(item['precio'])

        # Forma de Pago (B43-B44)
        sheet['B43'].set_value(f"BANCO: {emi['cuenta']}")
        sheet['B44'].set_value(f"IBAN: {emi['numero_cuenta']}")

        nombre_salida = f"Factura_{res['factura']}_{res['cliente'].capitalize()}.ods"
        ods.saveas(nombre_salida)
        print(f"SUCCESS: {nombre_salida}")

    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    generar()