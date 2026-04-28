# Skill: Facturación ODS 

## Description
Sistema de facturación local que calcula precios, valida presupuestos objetivo y genera archivos .ods basados en plantillas de cliente, actualizando automáticamente los contadores de factura.

## System Instructions / Rules
1. **FLUJO CRÍTICO**: 1º Escribir `input.txt` -> 2º Ejecutar `python mcp_facturacion.py` para validar nombres y precios de productos -> 3º Ejecutar `python completar_ods.py`.
2. **VALIDACIÓN DE OBJETIVO**: Tras el cálculo, informa al usuario del total. Si supera el "Objetivo", pregunta si desea proceder antes de generar el .ods.
3. **SELECCIÓN DE PLANTILLA**: El sistema usará automáticamente `plantilla_belinda.ods` o `plantilla_woven.ods` según el cliente.
4. **CONTADORES**: El sistema lee y actualiza `counters.json` automáticamente.

## Tools

### 1. ejecutar_calculo
**Description**: Escribe datos en `input.txt` y calcula totales.
**Instructions**:
1. Escribe en `input.txt`:
   Emisor: {{emisor}}
   Cliente: {{cliente}}
   Fecha: {{fecha}}
   Objetivo: {{objetivo}}
   Prendas: {{prendas_json}}
2. Ejecuta: `python mcp_facturacion.py`
3. Muestra al usuario la tabla con: Emisor, Cliente, Base, IVA y Total.

### 2. generar_ods_final
**Description**: Crea el archivo .ods físico una vez el cálculo es correcto.
**Instructions**:
1. Ejecuta: `python completar_ods.py`
2. Entrega al usuario el nombre del archivo generado.