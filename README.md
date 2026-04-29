# 🧵 FactuPro - Sistema de Facturación Textil

Sistema profesional de generación de facturas ODS para talleres de confección. Ejecutado sobre Streamlit con arquitectura modular.

## 🛡️ Seguridad y Acceso
* **Login Requerido:** Acceso protegido mediante `streamlit-authenticator`.
* **Cifrado de Contraseñas:** Las credenciales se almacenan mediante hashes Bcrypt en `config.yaml`.
* **Seguridad de Datos:** Información fiscal sensible centralizada en `data/counters.json`.

## 📂 Estructura del Software (SRE Design)
* `app.py`: Punto de entrada y orquestación de la UI.
* `src/auth.py`: Gestión de sesiones y autenticación de usuarios.
* `src/engine.py`: Motor de cálculo (mapeo de precios y aplicación de IVA).
* `src/bills_gen.py`: Generador de archivos ODS forzando el cálculo de valores.
* `src/utils.py`: Herramientas de limpieza de strings y formateo numérico.

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