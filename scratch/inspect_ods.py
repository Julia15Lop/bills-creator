import ezodf
import os

path = r"C:\Users\julia\OneDrive\FACTURAS ARTU\ARTURO\2026\ABRIL 2026\Factura_209_belinda_134051.ods"

if not os.path.exists(path):
    print("El archivo no existe en la ruta especificada.")
else:
    ods = ezodf.opendoc(path)
    sheet = ods.sheets[0]
    print(f"Dimensiones de la hoja: {sheet.nrows()} filas x {sheet.ncols()} columnas")
    
    # Imprimir todas las celdas con valores
    for r in range(sheet.nrows()):
        row_str = []
        for c in range(sheet.ncols()):
            val = sheet[r, c].value
            if val is not None:
                row_str.append(f"Row {r+1} Col {c+1}: {val}")
        if row_str:
            print(", ".join(row_str))
