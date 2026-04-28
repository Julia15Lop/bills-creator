import pandas as pd
import json
import re
import os
from datetime import datetime

def procesar():
    try:
        # 1. Leer input.txt
        with open('input.txt', 'r', encoding='utf-8') as f:
            text = f.read()

        # 2. Cargar Configuración y detectar entidades
        with open('counters.json', 'r+', encoding='utf-8') as f:
            contadores = json.load(f)
            emisor_id = "arturo" if "arturo" in text.lower() else "carmen"
            cliente_id = "belinda" if "belinda" in text.lower() else "woven"
            
            emisor_data = contadores[emisor_id]
            nuevo_num = emisor_data['ultimo_numero'] + 1
            fecha_hoy = datetime.now().strftime("%d/%m/%Y")
            
            objetivo = float(re.findall(r'Objetivo:\s*(\d+)', text)[0])
            prendas_input = json.loads(re.search(r'\{.*\}', text, re.DOTALL).group(0))

            # 3. Leer listado y filtrar por PRENDA + ID_CLIENTE
            df = pd.read_excel('listado_precios_clientes.ods', engine='odf')
            df.columns = [str(c).strip() for c in df.columns]
            
            items_finales = []
            total_acumulado = 0

            for nombre_buscado, tallas in prendas_input.items():
                # Filtro doble: Nombre de prenda Y Cliente
                mask = (df['NOMBRE ARTÍCULO'].str.contains(nombre_buscado, case=False, na=False)) & \
                       (df['ID_CLIENTE'].str.contains(cliente_id, case=False, na=False))
                fila = df[mask]
                
                if fila.empty:
                    continue # O podrías lanzar un error si no encuentra el precio para ese cliente
                
                nombre_oficial = fila.iloc[0]['NOMBRE ARTÍCULO']
                precio_unit = float(str(fila.iloc[0]['PRECIO CLIENTE']).replace('€','').replace(',','.'))
                
                for talla, cant in tallas.items():
                    # Formateo T-XX
                    t_num = str(talla).upper().replace('T','').replace('-','').strip()
                    item_total = precio_unit * cant
                    total_acumulado += item_total
                    
                    items_finales.append({
                        "desc": nombre_oficial,
                        "talla": f"T-{t_num}",
                        "cant": cant,
                        "precio": precio_unit
                    })

            # 4. Preparar resultado para la IA y el siguiente script
            resultado = {
                "factura": nuevo_num,
                "cliente": cliente_id,
                "fecha": fecha_hoy,
                "emisor": emisor_data,
                "items": items_finales,
                "total_estimado": round(total_acumulado * 1.21, 2), # Con IVA para validar objetivo
                "supera_objetivo": (total_acumulado * 1.21) > objetivo
            }
            
            with open('ultimo_resultado.json', 'w', encoding='utf-8') as f_res:
                json.dump(resultado, f_res, indent=2)

            # 5. Actualizar contador
            contadores[emisor_id]['ultimo_numero'] = nuevo_num
            f.seek(0); json.dump(contadores, f, indent=2); f.truncate()
            
            print(json.dumps(resultado, indent=2))

    except Exception as e:
        print(json.dumps({"status": "error", "msg": str(e)}))

if __name__ == "__main__":
    procesar()