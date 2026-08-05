# TourFlow

Aplicación web para gestionar giras y controlar su planificación financiera.

## Funcionalidades

- Inicio de sesión con rutas protegidas.
- Registro, consulta, edición y eliminación de giras.
- Dashboard con búsqueda y estadísticas.
- Validaciones de datos y mensajes de confirmación.
- Indicador financiero: Financiada, En progreso o Pendiente.
- Pruebas automatizadas con Selenium y reporte HTML.

## Tecnologías

Python, Flask, SQLite, Bootstrap, Selenium y PyTest.

## Ejecutar el proyecto

Requiere Python 3.10 o superior.

```powershell
.\run.ps1
```

Abre `http://127.0.0.1:5000` en el navegador.

Credenciales de demostración:

```text
Usuario: organizador
Contraseña: TourFlow123!
```

## Ejecutar las pruebas

Las pruebas levantan una instancia temporal de la aplicación y usan una base de datos independiente.

```powershell
.\run_tests.ps1
```

El reporte se genera en `reports/reporte.html` e incluye las capturas de los escenarios ejecutados.

El repositorio incluye este reporte y sus capturas como evidencia de la última ejecución.

Para observar la ejecución con pausas durante una demostración:

```powershell
$env:TOURFLOW_STEP_DELAY="0.5"
.\run_tests.ps1
```
