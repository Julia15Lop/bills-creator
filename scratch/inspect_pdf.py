import pypdf
import os

path = r"C:\Users\julia\OneDrive\FACTURAS ARTU\ARTURO\2026\MARZO 2026\FACTURA 207.pdf"

if not os.path.exists(path):
    print("El archivo no existe.")
else:
    reader = pypdf.PdfReader(path)
    print(f"Número de páginas: {len(reader.pages)}")
    text = reader.pages[0].extract_text()
    print("--- CONTENIDO DEL PDF ---")
    print(text)
