import json
import os
import sys
import pandas as pd
from datetime import datetime
from src.engine import procesar_factura
from src.bills_gen import generar_ods

def read_input():
    if not os.path.exists('input.txt'):
        print("Error: No se encuentra input.txt")
        sys.exit(1)
    
    data = {}
    with open('input.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    prendas_json = ""
    parsing_prendas = False
    
    for line in lines:
        if line.startswith('Emisor:'):
            data['emisor'] = line.split(':', 1)[1].strip().lower()
        elif line.startswith('Cliente:'):
            data['cliente'] = line.split(':', 1)[1].strip().lower()
        elif line.startswith('Fecha:'):
            data['fecha'] = line.split(':', 1)[1].strip()
        elif line.startswith('Objetivo:'):
            data['objetivo'] = float(line.split(':', 1)[1].strip())
        elif line.startswith('Prendas:'):
            parsing_prendas = True
            prendas_json = line.split(':', 1)[1].strip()
        elif parsing_prendas:
            prendas_json += line.strip()
            
    if prendas_json:
        data['prendas'] = json.loads(prendas_json)
    
    return data

def run_calculation():
    config = read_input()
    
    # Cargar datos necesarios
    PATH_COUNTERS = 'data/counters.json'
    PATH_PRECIOS = 'data/listado_precios_clientes.xlsx'
    
    if not os.path.exists(PATH_COUNTERS):
        print(f"Error: No se encuentra {PATH_COUNTERS}")
        sys.exit(1)
        
    with open(PATH_COUNTERS, 'r', encoding='utf-8') as f:
        contadores = json.load(f)
        
    if config['emisor'] not in contadores:
        print(f"Error: Emisor '{config['emisor']}' no encontrado en counters.json")
        sys.exit(1)
        
    emisor_data = contadores[config['emisor']]
    df_p = pd.read_excel(PATH_PRECIOS)
    
    # Procesar
    res = procesar_factura(
        config['emisor'], 
        config['cliente'], 
        config['fecha'], 
        config['objetivo'], 
        config['prendas'], 
        df_p, 
        emisor_data
    )
    
    # Guardar resultado temporal para el siguiente paso si es necesario
    with open('last_calc.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=2)
        
    # Mostrar resultados
    print("\n=== RESULTADO DEL CÁLCULO ===")
    print(f"Factura Nº: {res['factura']}")
    print(f"Emisor: {res['emisor']['nombre_fiscal']}")
    print(f"Cliente: {res['cliente']}")
    print(f"Fecha: {res['fecha']}")
    print("-" * 30)
    print(f"{'Descripción':<20} | {'Talla':<5} | {'Cant':<5} | {'Subtotal':<10}")
    for item in res['items']:
        print(f"{item['desc'][:20]:<20} | {item['talla']:<5} | {item['cant']:<5} | {item['subtotal']:<10.2f}€")
    print("-" * 30)
    print(f"TOTAL ESTIMADO (IVA INCL.): {res['total_estimado']:.2f}€")
    if res['supera_objetivo']:
        print(f"⚠️ AVISO: Supera el objetivo de {config['objetivo']}€")
    else:
        print(f"✅ Dentro del objetivo de {config['objetivo']}€")
    
    return res

def run_generation():
    if not os.path.exists('last_calc.json'):
        print("Error: No hay un cálculo previo. Ejecuta primero el cálculo.")
        sys.exit(1)
        
    with open('last_calc.json', 'r', encoding='utf-8') as f:
        res = json.load(f)
        
    ruta = generar_ods(res)
    
    # Actualizar contador
    PATH_COUNTERS = 'data/counters.json'
    with open(PATH_COUNTERS, 'r', encoding='utf-8') as f:
        contadores = json.load(f)
    
    emisor_key = res['emisor']['nombre_fiscal'].split()[0].lower() # Heuristic to find the key
    # Better: use the emisor key from input.txt if we saved it
    # For now, let's assume the user knows which one they are.
    # Actually, we should have saved the key in last_calc.json
    
    # Let's just find the emisor in contadores that matches the cif
    for key, data in contadores.items():
        if data['cif'] == res['emisor']['cif']:
            contadores[key]['ultimo_numero'] = res['factura']
            break
            
    with open(PATH_COUNTERS, 'w', encoding='utf-8') as f:
        json.dump(contadores, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ Factura generada con éxito: {ruta}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python run_engine.py [calc|gen]")
        sys.exit(1)
        
    mode = sys.argv[1]
    if mode == 'calc':
        run_calculation()
    elif mode == 'gen':
        run_generation()
    else:
        print("Modo no reconocido. Usa 'calc' o 'gen'.")
