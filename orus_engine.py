import cv2
import threading
import os
import time
import sqlite3
import numpy as np
import requests
from datetime import datetime
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
        
        print("[SISTEMA] > Cargando YOLOv8...")
        self.model = YOLO('yolov8n.pt')
        
        # Configuración Facial
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.nombres_autorizados = {}
        self.modelo_entrenado = False
        
        # --- VARIABLES FALTANTES RESTAURADAS ---
        self.last_notification_time = {} # Diccionario para controlar el spam
        self.cooldown_seconds = 30       # Segundos de espera entre alertas
        # ---------------------------------------

        # Zona prohibida
        self.zona_prohibida = np.array([[100, 480], [540, 480], [450, 250], [190, 250]], np.int32)
        
        self.notifier = None
        if tg_token and tg_chat_id:
            self.notifier = OrusNotifier(tg_token, tg_chat_id)

        # Crear directorios necesarios
        for d in [self.evidencia_dir, self.auth_dir]:
            if not os.path.exists(d): os.makedirs(d)
            
        self._init_db()
        self._entrenar_caras()

    def _entrenar_caras(self):
        """Entrena el modelo con todas las fotos en authorizedPerson."""
        print("[SISTEMA] > (Re)Entrenando modelo facial...")
        caras_entrenamiento = []
        ids = []
        current_id = 0
        self.nombres_autorizados = {} # Reiniciar mapeo

        archivos = [f for f in os.listdir(self.auth_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
        
        if not archivos:
            print("[INFO] > No hay base de datos facial. Modo 100% Intrusos.")
            self.modelo_entrenado = False
            return

        for archivo in archivos:
            path = os.path.join(self.auth_dir, archivo)
            nombre_base = os.path.splitext(archivo)[0].split('_')[0] 
            
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is None: continue
            
            # Detectar cara
            rostros = self.face_cascade.detectMultiScale(img, 1.1, 5)
            for (x, y, w, h) in rostros:
                caras_entrenamiento.append(img[y:y+h, x:x+w])
                ids.append(current_id)
                self.nombres_autorizados[current_id] = nombre_base
            
            if len(rostros) > 0:
                current_id += 1
        
        if len(ids) > 0:
            self.recognizer.train(caras_entrenamiento, np.array(ids))
            self.modelo_entrenado = True
            print(f"[SISTEMA] > Modelo actualizado: {len(ids)} muestras aprendidas.")
        else:
            self.modelo_entrenado = False

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY, timestamp TEXT, objeto_id TEXT, foto_path TEXT)")
            conn.commit()
            conn.close()
        except Exception: pass

    # --- FUNCIÓN DE APRENDIZAJE ---
    def capturar_nuevo_residente(self, frame_inicial): # Renombrado para evitar confusión
        print("\n" + "="*40)
        time.sleep(0.5) # Limpiar buffer de teclado
        
        try:
            nombre = input("[ENTRENAMIENTO] Ingrese nombre de la persona: ").strip().upper()
        except: return

        if not nombre: return

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
        cap = cv2.VideoCapture(0)
        while self.running:
            ret, frame = cap.read()
            if ret: self.frame = frame
            else: break
        cap.release()

    def iniciar_vigilancia(self):
        self.frame = None
        self.running = True
        threading.Thread(target=self._stream_reader, daemon=True).start()
        
        print("\n" + "*"*50)
        print("[SISTEMA] > ORUS VIGILANCIA ACTIVA")
        print("[COMANDO] > Presione 't' para ENTRENAR una cara nueva.")
        print("[COMANDO] > Presione 'q' para SALIR.")
        print("*"*50 + "\n")

        while self.running:
            if self.frame is None: continue
            current_frame = self.frame.copy()
            
            overlay = current_frame.copy()
            cv2.fillPoly(overlay, [self.zona_prohibida], (0, 0, 255))
            cv2.addWeighted(overlay, 0.4, current_frame, 0.6, 0, current_frame)

            results = self.model.track(current_frame, persist=True, classes=[0], verbose=False)

            if results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
                ids = results[0].boxes.id.cpu().numpy().astype(int)

                for box, obj_id in zip(boxes, ids):
                    px, py = int((box[0] + box[2]) / 2), int(box[3])
                    
                    if cv2.pointPolygonTest(self.zona_prohibida, (px, py), False) >= 0:
                        color, texto = self.procesar_sujeto(obj_id, current_frame, box)
                    else:
                        color, texto = (0, 255, 0), f"Persona #{obj_id}"
                    
                    cv2.rectangle(current_frame, (box[0], box[1]), (box[2], box[3]), color, 2)
                    cv2.putText(current_frame, texto, (box[0], box[1]-10), 0, 0.5, color, 2)

            cv2.putText(current_frame, "Presiona 't' para entrenar", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.imshow("SISTEMA ORUS - SECURITY", current_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.running = False
                break
            elif key == ord('t'):
                self.capturar_nuevo_residente(self.frame)

        cv2.destroyAllWindows()