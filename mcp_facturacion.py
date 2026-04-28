import pandas as pd
import json
import re
import os
from datetime import datetime

def limpiar_precio(valor):
    if pd.isna(valor): return 0.0
    # Eliminar €, espacios y ajustar comas por puntos
    s = str(valor).replace('€', '').replace(' ', '').replace(',', '.').strip()
    try:
        # Quedarse solo con números y el primer punto que encuentre
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except: return 0.0

def procesar():
    if os.path.exists('ultimo_resultado.json'): os.remove('ultimo_resultado.json')
    try:
        with open('input.txt', 'r', encoding='utf-8') as f: text = f.read()
        with open('counters.json', 'r', encoding='utf-8') as f: contadores = json.load(f)
        
        emisor_id = "arturo" if "arturo" in text.lower() else "carmen"
        cliente_id = "belinda" if "belinda" in text.lower() else "woven"
        emisor_data = contadores[emisor_id]
        
        # Fecha exacta del input
        match_fecha = re.search(r'Fecha:\s*(\d{2}/\d{2}/\d{4})', text)
        fecha_f = match_fecha.group(1) if match_fecha else datetime.now().strftime("%d/%m/%Y")
        
        # Objetivo
        obj_match = re.search(r'Objetivo:\s*([\d.]+)', text)
        objetivo = float(obj_match.group(1)) if obj_match else 2500.0
        
        prendas_input = json.loads(re.search(r'\{.*\}', text, re.DOTALL).group(0))
        df = pd.read_excel('listado_precios_clientes.ods', engine='odf')
        df.columns = [str(c).strip() for c in df.columns]
        
        items_finales = []
        total_base = 0

        for nombre_buscado, tallas in prendas_input.items():
            mask = (df['NOMBRE ARTÍCULO'].str.contains(re.escape(nombre_buscado), case=False, na=False)) & \
                   (df['ID_CLIENTE'].str.contains(cliente_id, case=False, na=False))
            fila = df[mask]
            
            if not fila.empty:
                p_unit = limpiar_precio(fila.iloc[0]['PRECIO CLIENTE'])
                for t, cant in tallas.items():
                    sub = p_unit * cant
                    total_base += sub
                    items_finales.append({"desc": fila.iloc[0]['NOMBRE ARTÍCULO'], "talla": t, "cant": cant, "precio": p_unit})

        nuevo_num = emisor_data['ultimo_numero'] + 1
        resultado = {
            "factura": nuevo_num, "cliente": cliente_id, "fecha": fecha_f,
            "emisor": emisor_data, "items": items_finales,
            "total_estimado": round(total_base * 1.21, 2),
            "supera_objetivo": (total_base * 1.21) > objetivo
        }
        
        with open('ultimo_resultado.json', 'w', encoding='utf-8') as f_res:
            json.dump(resultado, f_res, indent=2)

        contadores[emisor_id]['ultimo_numero'] = nuevo_num
        with open('counters.json', 'w', encoding='utf-8') as f_c: json.dump(contadores, f_c, indent=2)
            
    except Exception as e:
        with open('error_log.txt', 'w') as log: log.write(str(e))

if __name__ == "__main__":
    procesar()