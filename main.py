import time
import os
from orus_engine import OrusEngine, OrusNotifier
import requests
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    
    # Tus credenciales
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    print("--- ORUS SISTEMA DE VIGILANCIA ONLINE ---")
    
    if not TOKEN or not CHAT_ID:
        print("[ERROR] Faltan las credenciales de Telegram. Crea tu archivo .env basado en .env.example")
        exit(1)
    
    # --- PRUEBA DE CONEXIÓN INICIAL ---
    print("[TEST] Probando conexión con Telegram...")
    try:
        notificador_prueba = OrusNotifier(TOKEN, CHAT_ID)
        # Forzamos el envío de un mensaje de texto simple
        resp = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             data={'chat_id': CHAT_ID, 'text': "✅ ORUS: Sistema iniciado y conectado."})
        print(f"[TEST] Respuesta del servidor: {resp.status_code}")
        if resp.status_code == 200:
            print("[TEST] ¡ÉXITO! Mensaje enviado. Revisa tu celular.")
        else:
            print(f"[TEST] ERROR: {resp.text}")
    except Exception as e:
        print(f"[TEST] FALLÓ LA CONEXIÓN: {e}")
        print("POSIBLE SOLUCIÓN: Ejecuta 'pip install requests' en la terminal.")
    # -------------------------------------

    # Iniciar motor
    orus = OrusEngine(tg_token=TOKEN, tg_chat_id=CHAT_ID)
    
    # ¡A cruzar la zona roja!
    orus.iniciar_vigilancia()