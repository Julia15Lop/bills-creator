# 🧵 FactuPro - Sistema de Facturación Textil

Sistema profesional de generación de facturas ODS para talleres de confección. Ejecutado sobre Streamlit con arquitectura modular.

## 🛡️ Seguridad y Acceso
* **Login Requerido:** Acceso protegido mediante `streamlit-authenticator`. El usuario `admin`posee visibilidad total. 
* **Cifrado de Contraseñas:** Las credenciales se almacenan mediante hashes Bcrypt en `config.yaml`.
* **Seguridad de Datos:** Información fiscal sensible centralizada en `data/counters.json`.

## 📁 Estructura del Proyecto
- `app.py`: Punto de entrada y gestión de navegación.
- `views/`: Contiene las pantallas de la aplicación (Bills y Prices).
- `src/`: Lógica de negocio (Autenticación, Motor de Cálculo, Generador ODS).
- `data/`: Persistencia en archivos (Contadores JSON y Precios ODS).
- `output/`: Carpeta donde se depositan las facturas generadas.

## 🛠️ Instalación
1. `pip install -r requirements.txt`
2. Configurar usuarios en `config.yaml`.
3. Ejecutar: `streamlit run app.py`

## 🚀 Despliegue (Railway)
1. Conectar este repositorio a Railway.app.
2. Railway detectará el `Dockerfile` y expondrá la app en el puerto 8080.
3. Las facturas generadas se almacenan en el volumen persistente dentro de `/output`.

## 🛠️ Stack Tecnológico
- **Frontend:** Streamlit
- **Procesamiento:** Pandas & Python 3.11
- **Documentos:** ezodf (Open Document Spreadsheets)
- **Seguridad:** PyYAML & Bcrypt

---
**Desarrollado por Julia para optimización de procesos de facturación textiles.**