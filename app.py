import os
import time
import json
import sqlite3
import threading
# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
from flask import Flask, render_template, Response, request, jsonify
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from orus_engine import OrusEngine

app = Flask(__name__)

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Iniciar motor en un hilo separado
orus_instance = OrusEngine(tg_token=TOKEN, tg_chat_id=CHAT_ID)
threading.Thread(target=orus_instance.iniciar_vigilancia, daemon=True).start()

def generar_frames():
    """Generador para el streaming MJPEG de Flask con limitación de FPS."""
    while True:
        if orus_instance.output_frame is None:
            time.sleep(0.1)
            continue
            
        # Codificar el frame a JPEG
        ret, buffer = cv2.imencode('.jpg', orus_instance.output_frame)
        if not ret:
            time.sleep(0.03)
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # IMPORTANTE: Evita saturar el CPU y bloquear hilos por el GIL de Python
        time.sleep(0.03)

@app.route('/')
def index():
    """Ruta principal del Dashboard Web."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Ruta del stream MJPEG."""
    return Response(generar_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/train', methods=['POST'])
def entrenar_residente():
    """Endpoint para registrar un nuevo residente."""
    data = request.json
    nombre = data.get('nombre', '')
    if not nombre:
        return jsonify({"error": "Nombre requerido"}), 400
        
    # Iniciar la captura dinámica en un hilo
    threading.Thread(target=orus_instance.capturar_nuevo_residente, args=(nombre,), daemon=True).start()
    return jsonify({"success": True, "message": f"Iniciando entrenamiento para {nombre}"})

@app.route('/api/roi', methods=['POST', 'GET'])
def gestionar_roi():
    """Endpoint para actualizar o leer la zona ROI."""
    if request.method == 'POST':
        data = request.json
        puntos = data.get('puntos', [])
        if orus_instance.actualizar_zona_roi(puntos):
            return jsonify({"success": True, "message": "ROI actualizada"})
        return jsonify({"error": "Mínimo 3 puntos requeridos"}), 400
    
    return jsonify({"puntos": orus_instance.zona_prohibida.tolist() if orus_instance.zona_prohibida.size > 0 else []})

@app.route('/api/residents', methods=['GET', 'DELETE'])
def gestionar_residentes():
    """Endpoint para listar o eliminar residentes."""
    if request.method == 'GET':
        return jsonify({"residentes": orus_instance.obtener_residentes()})
    elif request.method == 'DELETE':
        nombre = request.json.get('nombre', '')
        if orus_instance.eliminar_residente(nombre):
            return jsonify({"success": True, "message": f"{nombre} eliminado"})
        return jsonify({"error": "No se pudo eliminar"}), 400

@app.route('/api/config', methods=['GET', 'POST'])
def gestionar_config():
    """Endpoint para leer/actualizar configuración general."""
    if request.method == 'GET':
        return jsonify({
            "cooldown_seconds": orus_instance.cooldown_seconds,
            "camera_index": orus_instance.camera_index
        })
    elif request.method == 'POST':
        data = request.json
        if 'cooldown_seconds' in data:
            orus_instance.cooldown_seconds = int(data['cooldown_seconds'])
        if 'camera_index' in data:
            orus_instance.camera_index = int(data['camera_index'])
        orus_instance._guardar_configuracion()
        return jsonify({"success": True, "message": "Configuración actualizada"})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Obtiene los últimos eventos de la base de datos."""
    try:
        conn = sqlite3.connect("orus_logs.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, timestamp, objeto_id, foto_path FROM eventos ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for r in rows:
            logs.append({
                "id": r[0],
                "timestamp": r[1],
                "objeto_id": r[2],
                "foto_path": r[3]
            })
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("[FLASK] > Iniciando servidor web de ORUS en http://localhost:5000")
    # debug=False importante para que OpenCV no colapse con el reloader automático de Flask
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
