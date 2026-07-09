# pyrefly: ignore [missing-import]
import cv2
import threading
import os
import time
import sqlite3
# pyrefly: ignore [missing-import]
import numpy as np
import requests
import json
from datetime import datetime
# pyrefly: ignore [missing-import]
from ultralytics import YOLO 

# Activar entorno virtual para ejecusion de modelo
# .\venv\Scripts\activate

class OrusNotifier:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.token}/"

    def enviar_alerta_telegram(self, mensaje, foto_path=None):
        def _enviar():
            try:
                if foto_path and os.path.exists(foto_path):
                    with open(foto_path, 'rb') as foto:
                        requests.post(self.api_url + "sendPhoto", 
                                        data={'chat_id': self.chat_id, 'caption': mensaje},
                                        files={'photo': foto})
                else:
                    requests.post(self.api_url + "sendMessage", 
                                    data={'chat_id': self.chat_id, 'text': mensaje})
            except Exception as e:
                print(f"\n[!!! ERROR CRÍTICO TELEGRAM !!!] > {e}\n")

        threading.Thread(target=_enviar, daemon=True).start()

class OrusEngine:
    def __init__(self, tg_token=None, tg_chat_id=None):
        self.db_name = "orus_logs.db"
        self.evidencia_dir = "evidencia"
        self.auth_dir = "authorizedPerson"
        self.config_file = "config.json"
        
        # Variables de estado ROI
        self.dibujando_roi = False
        self.roi_puntos_temp = []
        
        self._cargar_configuracion()
        
        print("[SISTEMA] > Cargando YOLOv8...")
        self.model = YOLO('yolov8n.pt')
        
        # Configuración Facial
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.nombres_autorizados = {}
        self.modelo_entrenado = False
        
        self.last_notification_time = {} # Diccionario para controlar el spam
        
        self.notifier = None
        if tg_token and tg_chat_id:
            self.notifier = OrusNotifier(tg_token, tg_chat_id)

        # Crear directorios necesarios
        for d in [self.evidencia_dir, self.auth_dir]:
            if not os.path.exists(d): os.makedirs(d)
            
        self._init_db()
        self._entrenar_caras()

    def _cargar_configuracion(self):
        self.cooldown_seconds = 30
        self.camera_index = 0
        self.zona_prohibida = np.array([[100, 480], [540, 480], [450, 250], [190, 250]], np.int32)
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    self.cooldown_seconds = config.get("cooldown_seconds", 30)
                    self.camera_index = config.get("camera_index", 0)
                    roi_pts = config.get("roi_polygon", [])
                    if len(roi_pts) >= 3:
                        self.zona_prohibida = np.array(roi_pts, np.int32)
                    elif len(roi_pts) == 0:
                        self.zona_prohibida = np.array([], np.int32)
            except Exception as e:
                print(f"[WARN] Error cargando config.json: {e}")

    def _guardar_configuracion(self):
        config = {
            "cooldown_seconds": self.cooldown_seconds,
            "camera_index": self.camera_index,
            "roi_polygon": self.zona_prohibida.tolist() if self.zona_prohibida.size > 0 else []
        }
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=4)

    def _entrenar_caras(self):
        """Entrena el modelo con todas las fotos en authorizedPerson."""
        print("[SISTEMA] > (Re)Entrenando modelo facial...")
        caras_entrenamiento = []
        ids = []
        
        nombres_a_id = {}
        siguiente_id = 1
        self.nombres_autorizados = {} # Reiniciar mapeo

        archivos = [f for f in os.listdir(self.auth_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
        
        if not archivos:
            print("[INFO] > No hay base de datos facial. Modo 100% Intrusos.")
            self.modelo_entrenado = False
            return

        for archivo in archivos:
            path = os.path.join(self.auth_dir, archivo)
            nombre_base = os.path.splitext(archivo)[0].split('_')[0] 
            
            if nombre_base not in nombres_a_id:
                nombres_a_id[nombre_base] = siguiente_id
                self.nombres_autorizados[siguiente_id] = nombre_base
                siguiente_id += 1
                
            current_id = nombres_a_id[nombre_base]
            
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is None: continue
            
            # Las fotos guardadas ya están recortadas con padding, intentamos detectar
            rostros = self.face_cascade.detectMultiScale(img, 1.1, 4, minSize=(30, 30))
            if len(rostros) > 0:
                (x, y, w, h) = max(rostros, key=lambda b: b[2] * b[3])
                caras_entrenamiento.append(img[y:y+h, x:x+w])
                ids.append(current_id)
            else:
                # Fallback: toda la imagen es la cara
                caras_entrenamiento.append(img)
                ids.append(current_id)
        
        if len(ids) > 0:
            self.recognizer.train(caras_entrenamiento, np.array(ids))
            self.modelo_entrenado = True
            print(f"[SISTEMA] > Modelo actualizado: {len(ids)} muestras aprendidas de {len(nombres_a_id)} residentes.")
        else:
            self.modelo_entrenado = False

    def obtener_residentes(self):
        return list(set(self.nombres_autorizados.values()))
        
    def eliminar_residente(self, nombre):
        nombre = nombre.strip().upper()
        archivos = os.listdir(self.auth_dir)
        eliminados = 0
        for f in archivos:
            if f.startswith(f"{nombre}_"):
                try:
                    os.remove(os.path.join(self.auth_dir, f))
                    eliminados += 1
                except: pass
        if eliminados > 0:
            self._entrenar_caras()
            return True
        return False

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY, timestamp TEXT, objeto_id TEXT, foto_path TEXT)")
            conn.commit()
            conn.close()
        except Exception: pass

    # --- FUNCIÓN DE APRENDIZAJE ---
    def capturar_nuevo_residente(self, nombre):
        print("\n" + "="*40)
        
        if not nombre: 
            return
            
        nombre = nombre.strip().upper()
        if not nombre:
            return

        print(f"[ENTRENAMIENTO] Iniciando captura dinámica para {nombre}...")
        print(">> POR FAVOR: Mueve ligeramente la cabeza, sonríe, ponte serio mientras capturamos.")
        time.sleep(1) # Tiempo para prepararse

        count = 0
        objetivo = 40 # Aumentamos a 40 fotos para mejor calidad
        
        while count < objetivo:
            # 1. CRÍTICO: Usamos el frame ACTUAL del video en vivo, no el estático
            if self.frame is None: continue
            frame_vivo = self.frame.copy()
            
            # 2. Convertir a gris para detectar
            gray = cv2.cvtColor(frame_vivo, cv2.COLOR_BGR2GRAY)
            rostros = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50,50))

            # 3. Solo guardamos si detectamos una cara en el frame actual
            if len(rostros) > 0:
                # Tomamos la cara más grande (por si hay gente atrás)
                (x, y, w, h) = max(rostros, key=lambda b: b[2] * b[3])
                
                # Expandir un poco el recorte (Padding) para que no quede muy ajustado
                padding = 20
                y1 = max(0, y - padding)
                y2 = min(frame_vivo.shape[0], y + h + padding)
                x1 = max(0, x - padding)
                x2 = min(frame_vivo.shape[1], x + w + padding)
                
                face_img = frame_vivo[y1:y2, x1:x2]
                
                if face_img.size > 0:
                    # Guardar archivo
                    timestamp = datetime.now().strftime('%H%M%S%f')
                    ruta = os.path.join(self.auth_dir, f"{nombre}_{timestamp}.jpg")
                    cv2.imwrite(ruta, face_img)
                    
                    count += 1
                    
                    # Visual feedback en consola
                    print(f"   -> Captura {count}/{objetivo} OK (Muevete un poco...)")
                    
                    # Pequeña pausa para permitirte mover la cara y que no sean idénticas
                    time.sleep(0.15) 
            else:
                print("   [!] No veo tu cara, acércate...")

        print(f"[ENTRENAMIENTO] ¡Listo! {count} muestras variadas guardadas.")
        print("[SISTEMA] Re-entrenando IA con los nuevos datos...")
        self._entrenar_caras()
        print("="*40 + "\n")
    
    def es_autorizado(self, frame_sujeto):
        if not self.modelo_entrenado: return False, "Sin Datos"

        gray = cv2.cvtColor(frame_sujeto, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        
        rostros = self.face_cascade.detectMultiScale(gray, 1.05, 3, minSize=(30, 30))
        for (x, y, w, h) in rostros:
            rostro_roi = gray[y:y+h, x:x+w]
            try:
                id_predicho, confianza = self.recognizer.predict(rostro_roi)
                if confianza < 80: 
                    nombre = self.nombres_autorizados.get(id_predicho, "Autorizado")
                    return True, nombre
            except: pass
        return False, "Desconocido"

    def procesar_sujeto(self, obj_id, frame_original, bbox):
        x1, y1, x2, y2 = bbox
        
        # ZOOM INTELIGENTE
        altura_persona = y2 - y1
        y2_cabeza = y1 + int(altura_persona * 0.4)
        h_img, w_img, _ = frame_original.shape
        recorte_cabeza = frame_original[max(0, y1-20):min(h_img, y2_cabeza), max(0, x1-10):min(w_img, x2+10)]
        
        if recorte_cabeza.size > 0:
            es_auth, nombre = self.es_autorizado(recorte_cabeza)
            if es_auth: return (255, 255, 0), f"RESIDENTE: {nombre}"
            
        es_auth_full, nombre_full = self.es_autorizado(frame_original[y1:y2, x1:x2])
        if es_auth_full: return (255, 255, 0), f"RESIDENTE: {nombre_full}"

        self.enviar_alerta(obj_id, frame_original)
        return (0, 0, 255), f"INTRUSO #{obj_id}"

    def enviar_alerta(self, obj_id, frame):
        ahora_unix = time.time()
        if ahora_unix - self.last_notification_time.get(obj_id, 0) > self.cooldown_seconds:
            self.last_notification_time[obj_id] = ahora_unix
            foto_path = os.path.join(self.evidencia_dir, f"ALERTA_{obj_id}_{datetime.now().strftime('%H%M%S')}.jpg")
            cv2.imwrite(foto_path, frame)
            
            if self.notifier:
                self.notifier.enviar_alerta_telegram(f"🚨 ¡ALERTA ORUS!\nIntruso NO Reconocido (ID: #{obj_id})", foto_path)
            print(f"[ALERTA] > Intrusión enviada.")

    def _stream_reader(self):
        cap = None
        indices_a_probar = [0, 1, 2]
        
        # cv2.CAP_MSMF: Microsoft Media Foundation (nativo para Win10/11 y cámaras USB modernas)
        # cv2.CAP_ANY: Automático por si falla el anterior
        backends = [cv2.CAP_MSMF, cv2.CAP_ANY] 
        
        for backend in backends:
            if cap is not None:
                break
            
            backend_name = "Media Foundation (MSMF)" if backend == cv2.CAP_MSMF else "Automático"
            print(f"\n[SISTEMA] > Probando motor de captura: {backend_name}")
            
            for index in indices_a_probar:
                print(f"   -> Intentando conectar al índice {index}...")
                
                # Evita que OpenCV envíe logs molestos a la consola si falla la prueba
                temp_cap = cv2.VideoCapture(index, backend)
                
                if temp_cap.isOpened():
                    # Lectura de prueba real para descartar cámaras virtuales en negro
                    ret, frame = temp_cap.read()
                    if ret:
                        print(f"[SISTEMA] > ¡ÉXITO! Cámara Philco lista en índice {index} usando {backend_name}.")
                        cap = temp_cap
                        break
                
                # Liberamos el intento fallido
                temp_cap.release()

        # Si agotó todas las combinaciones y no hay cámara
        if cap is None:
            print("\n[!!! ERROR CRÍTICO !!!] > Imposible conectar con la cámara.")
            print("1. Desconecta y vuelve a conectar el USB.")
            print("2. Asegúrate de que la aplicación Cámara de Windows esté CERRADA.")
            self.running = False
            return

        # Bucle principal de lectura
        while self.running:
            ret, frame = cap.read()
            if ret: 
                self.frame = frame
            else: 
                print("\n[ERROR] > Se perdió la conexión de video de repente.")
                break
                
        cap.release()

    def actualizar_zona_roi(self, puntos):
        if len(puntos) >= 3:
            self.zona_prohibida = np.array(puntos, np.int32)
            self._guardar_configuracion()
            print("[SISTEMA] Zona ROI actualizada vía API.")
            return True
        return False

    def iniciar_vigilancia(self):
        self.frame = None
        self.output_frame = None
        self.running = True
        threading.Thread(target=self._stream_reader, daemon=True).start()
        
        print("\n[SISTEMA] > ORUS ENGINE STREAMING (Headless Web Mode)")

        while self.running:
            if self.frame is None: 
                time.sleep(0.01)
                continue
            current_frame = self.frame.copy()
            
            overlay = current_frame.copy()
            
            if self.zona_prohibida.size > 0:
                cv2.fillPoly(overlay, [self.zona_prohibida], (0, 0, 255))
                cv2.addWeighted(overlay, 0.4, current_frame, 0.6, 0, current_frame)

            results = self.model.track(current_frame, persist=True, classes=[0], verbose=False)

            if results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
                ids = results[0].boxes.id.cpu().numpy().astype(int)

                for box, obj_id in zip(boxes, ids):
                    px, py = int((box[0] + box[2]) / 2), int(box[3])
                    
                    adentro = False
                    if self.zona_prohibida.size > 0:
                        if cv2.pointPolygonTest(self.zona_prohibida, (px, py), False) >= 0:
                            adentro = True
                    
                    if adentro:
                        color, texto = self.procesar_sujeto(obj_id, current_frame, box)
                    else:
                        color, texto = (0, 255, 0), f"Persona #{obj_id}"
                    
                    cv2.rectangle(current_frame, (box[0], box[1]), (box[2], box[3]), color, 2)
                    cv2.putText(current_frame, texto, (box[0], box[1]-10), 0, 0.5, color, 2)

            self.output_frame = current_frame
            time.sleep(0.03) # Cap FPS para web