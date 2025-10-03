Tarea 1: Sistema de Caché Distribuido con Ollama y MySQL 

Este documento describe los pasos necesarios para la correcta configuración y ejecución del proyecto de Sistemas Distribuidos, asegurando que todos los componentes, incluido el modelo de lenguaje (LLM) `phi3`, estén listos.

---

## Requisitos y Preparación

Para ejecutar este proyecto sin fallos, es imprescindible cumplir con los siguientes requisitos previos:

### 1. Instalación de Docker

Asegúrate de tener **Docker Desktop** instalado y en ejecución en tu sistema operativo (Docker para Windows, macOS o Linux).

### 2. Instalación del Modelo de Lenguaje (Ollama)

El proyecto depende del modelo **`phi3`** dentro del contenedor de Ollama. Si el modelo no está ya instalado, sigue estos pasos:

1.  **Verificar el servicio:** Asegúrate de que el contenedor de Ollama esté encendido y en ejecución.
2.  **Acceder al Contenedor:** Utiliza el siguiente comando para ingresar a la terminal del contenedor:

    ```bash
    docker exec -it ollama bash
    ```

3.  **Descargar el Modelo:** Dentro de la terminal del contenedor, descarga el modelo `phi3`:

    ```bash
    ollama pull phi3
    ```

4.  **Verificación (Opcional):** Confirma que el modelo se haya instalado correctamente:

    ```bash
    ollama list
    ```

### 3. Requisito de Almacenamiento

El sistema requiere espacio de disco suficiente para el almacenamiento de:
* La imagen y el contenedor de **Ollama** (incluyendo el modelo `phi3`).
* La base de datos **MySQL** con los datos de caché.

---

Una vez completados los pasos de configuración y asegurado el espacio de almacenamiento, el programa puede ser ejecutado sin riesgo de fallos por dependencias.
