# 👁️ ORUS - AI Perimeter Surveillance System

> Sistema inteligente de vigilancia perimetral basado en Inteligencia Artificial, visión computacional y reconocimiento facial en tiempo real.

ORUS es una plataforma de seguridad desarrollada en Python que combina detección de personas, reconocimiento facial y monitoreo de zonas restringidas para identificar posibles intrusos y generar alertas automáticas con evidencia fotográfica mediante Telegram.

Su objetivo es proporcionar una solución de vigilancia autónoma, ligera y fácil de implementar en hogares, oficinas, bodegas y áreas de acceso restringido.

---

## ✨ Características

### 🎯 Detección Inteligente de Personas

Utiliza **YOLOv8** para detectar personas en tiempo real con alta precisión, ignorando mascotas, vehículos y otros objetos irrelevantes.

### 📍 Zonas de Vigilancia (ROI)

Define áreas restringidas mediante polígonos virtuales.

ORUS solamente genera alertas cuando una persona ingresa físicamente a la zona protegida, reduciendo significativamente los falsos positivos.

### 🧠 Reconocimiento Facial

Implementa el algoritmo **LBPH (Local Binary Pattern Histogram)** de OpenCV para distinguir entre:

* ✅ Residentes autorizados
* 🚨 Personas desconocidas
* ⚠️ Posibles intrusos

### 🎓 Aprendizaje en Vivo

Permite registrar nuevos residentes sin detener el sistema.

Con una sola tecla:

* Detecta automáticamente el rostro.
* Captura múltiples imágenes desde distintos ángulos.
* Reentrena el modelo facial en segundos.

### 📸 Evidencia Fotográfica

Cada detección genera automáticamente:

* Captura de pantalla.
* Fecha y hora del evento.
* Registro persistente para auditoría.

### 📲 Alertas por Telegram

Envía notificaciones instantáneas directamente al teléfono móvil mediante un Bot de Telegram.

Las alertas incluyen:

* Imagen del evento.
* Nombre identificado (si existe).
* Fecha y hora.
* Nivel de alerta.

### ⚡ Arquitectura Asíncrona

Las notificaciones se procesan en hilos independientes (*threading*), evitando bloqueos en el procesamiento de video.

### 🛡️ Protección Anti-Spam

Sistema de cooldown configurable que evita múltiples alertas consecutivas para el mismo individuo.

### 🗄️ Registro de Eventos

Todos los eventos quedan almacenados en una base de datos SQLite local para análisis posterior.

---

# 🏗️ Arquitectura General

```text
Cámara
   │
   ▼
YOLOv8
(Detección de Personas)
   │
   ▼
Validación de Zona ROI
   │
   ▼
Reconocimiento Facial (LBPH)
   │
   ├── Persona Autorizada
   │       └── Registrar Evento
   │
   └── Desconocido
           ├── Capturar Evidencia
           ├── Guardar en SQLite
           └── Enviar Alerta Telegram
```

---

# 🛠️ Tecnologías Utilizadas

| Tecnología   | Descripción                   |
| ------------ | ----------------------------- |
| Python 3.12+ | Lenguaje principal            |
| YOLOv8       | Detección de personas         |
| OpenCV       | Procesamiento de imágenes     |
| LBPH         | Reconocimiento facial         |
| SQLite       | Persistencia local            |
| NumPy        | Manipulación de datos         |
| Requests     | Comunicación con Telegram API |

---

# ⚙️ Instalación y Configuración

Sigue estos pasos para poner en marcha el sistema en tu entorno local.

## 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/Proyecto-ORUS-IA.git
cd Proyecto-ORUS-IA
```

## 2. Crear y activar el entorno virtual (Recomendado)

### Windows

```bash
python -m venv venv
.\venv\Scripts\activate
```

### Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

## 3. Instalar dependencias

El proyecto incluye un archivo `requirements.txt` para instalar de forma sencilla todas las dependencias necesarias (incluyendo Flask para el Dashboard Web):

```bash
pip install -r requirements.txt
```

Si prefieres instalar cada dependencia manualmente:

```bash
pip install ultralytics opencv-contrib-python requests numpy python-dotenv flask
```

---

# 📲 Configuración de Telegram

ORUS utiliza Telegram para enviar alertas en tiempo real con evidencia fotográfica.

## Crear un Bot

1. Abre Telegram y busca a **@BotFather**.
2. Ejecuta el comando:
   ```text
   /newbot
   ```
3. Sigue las instrucciones para asignarle un nombre y un nombre de usuario a tu Bot.
4. Guarda el **Token de API** que te proporcionará BotFather.

## Obtener tu Chat ID

1. Busca en Telegram al bot **@userinfobot**.
2. Presiona en /start o envíale cualquier mensaje.
3. Copia el valor numérico de tu **Id**.

## Configurar el archivo de Variables de Entorno (`.env`)

Para evitar exponer tus credenciales sensibles al subir el código a GitHub, el proyecto utiliza variables de entorno. 

Crea una copia de `.env.example` en la raíz del proyecto, nombrala `.env` e ingresa tus credenciales:

```bash
# Archivo .env
TELEGRAM_TOKEN=TU_TOKEN_AQUI
TELEGRAM_CHAT_ID=TU_CHAT_ID_AQUI
```

*(Nota: El archivo `.env` está configurado en `.gitignore` para no ser subido al repositorio público).*

---

# 🚀 Modos de Ejecución

ORUS puede iniciarse en dos modos distintos según tus necesidades:

## Opción A: Dashboard Web (Recomendado)
Inicia un servidor Flask local con una interfaz web interactiva para visualizar el streaming en vivo de la cámara, el historial de alertas y las configuraciones dinámicas.

1. Ejecuta el servidor de Flask:
   ```bash
   python app.py
   ```
2. Abre tu navegador web y entra a:
   [http://localhost:5000](http://localhost:5000)
3. Podrás interactuar con el Dashboard, visualizar la cámara en tiempo real y ver las alertas más recientes.

## Opción B: Modo Consola / Escritorio Directo
Si prefieres ejecutar el sistema de forma más ligera sin servidor web, utilizando directamente la ventana de OpenCV en tu escritorio.

1. Ejecuta el script principal:
   ```bash
   python main.py
   ```
2. Se abrirá una ventana de visualización local y verás las terminales de control e información de conexión a Telegram en la consola.


---

# 🎓 Registro de Nuevos Residentes

Por defecto, todas las personas serán consideradas desconocidas.

Para registrar un residente:

### Paso 1

Ubícate frente a la cámara.

### Paso 2

Presiona:

```text
T
```

### Paso 3

Ingresa tu nombre en la consola.

Ejemplo:

```text
Ingrese nombre:
Joaquin
```

### Paso 4

Mueve ligeramente la cabeza:

* Izquierda
* Derecha
* Arriba
* Abajo

También puedes variar:

* Expresión facial
* Distancia
* Ángulo

ORUS capturará aproximadamente 40 imágenes para entrenar un modelo más robusto.

### Paso 5

El sistema reentrenará automáticamente el reconocedor facial.

A partir de ese momento dejarás de ser identificado como intruso.

---

# ⌨️ Controles

| Tecla | Acción                         |
| ----- | ------------------------------ |
| T     | Registrar nuevo residente      |
| R     | Activar dibujo de zona ROI     |
| ENTER | Guardar la zona dibujada       |
| Q     | Cerrar sistema de forma segura |

## Configuración Dinámica

- **Zona Restringida (ROI)**: Presiona `R`, dibuja la zona haciendo clics con el mouse en la ventana de video y presiona `ENTER` para guardar. Se almacenará en `config.json`.
- **Registro No Bloqueante**: Al presionar `T`, se abrirá una ventana emergente para ingresar el nombre sin congelar el video.

---

# 📁 Estructura del Proyecto

```text
Proyecto-ORUS-IA/
│
├── .env.example            # Plantilla para variables de entorno de Telegram
├── .gitignore              # Configuración de archivos excluidos en Git
├── app.py                  # Servidor Flask (Dashboard Web)
├── main.py                 # Script ejecutable principal (Modo Consola/Escritorio)
├── orus_engine.py          # Motor de procesamiento de IA y reconocimiento facial
├── requirements.txt        # Dependencias de Python necesarias para el proyecto
│
├── config.json             # Parámetros de ROI y cámara (generado automáticamente)
├── orus_logs.db            # Historial de eventos en SQLite (generado automáticamente)
├── yolov8n.pt              # Pesos del modelo YOLOv8 (descargado automáticamente)
│
├── authorizedPerson/       # Dataset de rostros registrados de residentes (ignorada)
├── evidencia/              # Capturas fotográficas de intrusos (ignorada)
├── static/                 # Recursos de estilo y scripts de la interfaz web (CSS/JS)
├── templates/              # Plantilla HTML para la interfaz web (index.html)
└── README.md               # Documentación del proyecto
```

---

# 🗄️ Archivos Generados Automáticamente

| Archivo / Carpeta | Tipo | Descripción | ¿Subir a Git? |
| :--- | :--- | :--- | :--- |
| `evidencia/` | Carpeta | Capturas de pantalla e imágenes de intrusos detectados. | ❌ No (Ignorado) |
| `authorizedPerson/` | Carpeta | Imágenes del dataset de rostros autorizados de residentes. | ❌ No (Ignorado) |
| `config.json` | Archivo | Parámetros locales de cámara y coordenadas de la zona ROI dibujada. | ❌ No (Ignorado) |
| `orus_logs.db` | Archivo | Base de datos SQLite que guarda los registros locales de eventos. | ❌ No (Ignorado) |
| `yolov8n.pt` | Archivo | Modelo YOLOv8 preentrenado. Se descarga automáticamente de internet si no existe. | ❌ No (Ignorado) |

---

# 🔒 Configuración del `.gitignore`

El proyecto cuenta con un archivo `.gitignore` en la raíz que previene la subida accidental de archivos temporales, configuraciones específicas de hardware, claves de seguridad y bases de datos locales. La estructura configurada es:

```gitignore
# Entornos virtuales
venv/
env/

# Variables de entorno y credenciales sensibles
.env

# Base de datos local
orus_logs.db

# Configuración local de cámara y zonas ROI
config.json

# Dataset y capturas de personas/evidencia (Generados dinámicamente)
authorizedPerson/
evidencia/

# Modelos y pesos de IA (Descargados automáticamente en ejecución)
*.pt

# Caché de Python
__pycache__/
*.pyc

# Archivos temporales del sistema operativo
.DS_Store
Thumbs.db
```


---

# 🚧 Roadmap

## Próximas funcionalidades

* [ ] Panel Web de administración
* [ ] Dashboard en tiempo real
* [ ] Integración con cámaras IP (RTSP)
* [ ] Soporte para múltiples cámaras
* [ ] Reconocimiento facial con Deep Learning
* [ ] Exportación de eventos a CSV
* [ ] Integración con Discord
* [ ] Aplicación móvil

---

# 🤝 Contribuciones

Las contribuciones son bienvenidas.

Si deseas colaborar:

1. Haz un Fork del repositorio.
2. Crea una rama para tu funcionalidad.

```bash
git checkout -b feature/nueva-funcionalidad
```

3. Realiza tus cambios.
4. Envía un Pull Request.

---

# 📜 Licencia

Este proyecto se distribuye bajo licencia MIT.

Consulta el archivo:

```text
LICENSE
```

para más información.

---

# ⭐ Apoya el Proyecto

Si ORUS te resulta útil:

* Deja una estrella ⭐ en GitHub.
* Comparte el proyecto.
* Reporta errores.
* Propón nuevas funcionalidades.

Tu apoyo ayuda a seguir mejorando el proyecto.

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![YOLOv8](https://img.shields.io/badge/YOLO-v8-green)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-red)
![License](https://img.shields.io/badge/License-MIT-yellow)
