# Proyecto de Facturación Inteligente - Agent Kit

[cite_start]Sistema basado en **Antigravity** y **Model Context Protocol (MCP)** para la automatización de facturas de taller de costura[cite: 1, 3].

## 📂 Estructura de Archivos
* [cite_start]`counters.json`: Contiene los datos fiscales de mi cliente, junto al número de la última factura emitida.
* [cite_start]`Precios_Maestro.ods`: Base de datos con los precios por prenda, cliente y temporada[cite: 5].
* `Plantillas/`: Carpeta con los modelos de factura en formato ODS para cada cliente.

## 🚀 Funcionamiento
1. **Entrada:** El usuario introduce un prompt con las prendas hechas y el objetivo de facturación (ej: ~2500€).
2. **Cálculo:** El agente usa la Skill para buscar precios, sumar el IVA y proponer un borrador.
3. **Validación:** El agente pregunta: "¿El total de [X]€ con IVA te parece correcto?".
4. [cite_start]**Generación:** Si el usuario acepta, se actualiza el contador y se genera la factura final y el recibo de la costurera.

## 🛠️ Configuración
Para añadir este agente a tu entorno:
1. [cite_start]Copia la carpeta de la skill en `/skills/textile-invoicing/`.
2. Asegúrate de que el servidor MCP tiene permisos de lectura/escritura sobre `counters.json`.
3. Configura las rutas de las plantillas ODS en el archivo de configuración del agente.

---
**Desarrollado para optimización de procesos en talleres de confección.**