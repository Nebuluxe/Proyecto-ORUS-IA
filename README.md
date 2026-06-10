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

# ⚙️ Instalación

## 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/Proyecto-ORUS-IA.git

cd Proyecto-ORUS-IA
```

## 2. Crear entorno virtual

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

```bash
pip install ultralytics
pip install opencv-contrib-python
pip install requests
pip install numpy
```

O utilizando un archivo requirements:

```bash
pip install -r requirements.txt
```

---

# 📲 Configuración de Telegram

ORUS utiliza Telegram para enviar alertas en tiempo real.

## Crear un Bot

1. Abrir Telegram.
2. Buscar **@BotFather**.
3. Ejecutar:

```text
/newbot
```

4. Seguir las instrucciones.
5. Guardar el token generado.

---

## Obtener tu Chat ID

1. Buscar **@userinfobot**.
2. Enviar cualquier mensaje.
3. Copiar el valor de:

```text
Chat ID
```

---

## Configurar credenciales

Editar el archivo principal:

```python
if __name__ == "__main__":

    TOKEN = "TU_TOKEN_AQUI"

    CHAT_ID = "TU_CHAT_ID_AQUI"
```

---

# 🚀 Ejecución

Iniciar ORUS:

```bash
python main.py
```

Una vez iniciado:

* Se activará la cámara.
* Comenzará la detección de personas.
* Se cargará el modelo facial existente.
* Se activará el monitoreo de la zona protegida.

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
| Q     | Cerrar sistema de forma segura |

---

# 📁 Estructura del Proyecto

```text
Proyecto-ORUS-IA/
│
├── main.py
├── orus_logs.db
├── yolov8n.pt
│
├── evidencia/
│   └── capturas de intrusos
│
├── authorizedPerson/
│   └── rostros autorizados
│
└── README.md
```

---

# 🗄️ Archivos Generados Automáticamente

| Archivo           | Descripción                            |
| ----------------- | -------------------------------------- |
| evidencia/        | Evidencias fotográficas                |
| authorizedPerson/ | Dataset de residentes                  |
| orus_logs.db      | Historial de eventos                   |
| yolov8n.pt        | Modelo YOLO descargado automáticamente |

---

# 🔒 Configuración Recomendada de .gitignore

```gitignore
# Entornos virtuales
venv/
env/

# Caché Python
__pycache__/
*.pyc

# Datos generados por ORUS
evidencia/
authorizedPerson/

# Base de datos
orus_logs.db

# Modelos IA
*.pt

# Sistema operativo
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
