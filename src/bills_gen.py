import ezodf
from datetime import datetime

def generar_ods(res):
    plantilla = f"templates/plantilla_{res['cliente']}.ods"
    ods = ezodf.opendoc(plantilla)
    sheet = ods.sheets[0]
    emi = res['emisor']

    # Datos Emisor
    sheet['B10'].set_value(emi['nombre_fiscal'])
    sheet['B11'].set_value(f"CIF: {emi['cif']}")
    sheet['B12'].set_value(emi['direccion'])
    sheet['B13'].set_value(emi['codigo_postal'])
    sheet['B14'].set_value(f"Teléfono: {emi['telefono']}")
    sheet['B15'].set_value(f"Email: {emi['mail']}")

    # Encabezado
    sheet['E3'].set_value(f"N.º {res['factura']}")
    sheet['G5'].set_value(res['fecha'])

    # Ítems: Escribimos el subtotal para que no dependa de la fórmula
    for i, item in enumerate(res['items']):
        fila_idx = 19 + i
        sheet[f'B{fila_idx}'].set_value(item['desc'])
        sheet[f'C{fila_idx}'].set_value(item['talla'])
        sheet[f'E{fila_idx}'].set_value(item['cant'])
        sheet[f'F{fila_idx}'].set_value(item['precio'])
        sheet[f'G{fila_idx}'].set_value(item['subtotal']) # <--- AQUÍ forzamos el cálculo

    # Datos Pago
    sheet['B43'].set_value(f"BANCO: {emi['cuenta']}")
    sheet['B44'].set_value(f"IBAN: {emi['numero_cuenta']}")

    nombre_salida = f"Factura_{res['factura']}_{res['cliente']}_{datetime.now().strftime('%H%M%S')}.ods"
    ods.saveas(nombre_salida)
    return nombre_salida