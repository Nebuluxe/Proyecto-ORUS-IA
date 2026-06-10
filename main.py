import time
from orus_engine import OrusEngine, OrusNotifier
import requests

if __name__ == "__main__":
    # Tus credenciales
    TOKEN = "TU_TOKEN_DE_TELEGRAM_AQUI"  # Reemplaza con tu token real
    CHAT_ID = "TU_CHAT_ID_DE_TELEGRAM_AQUI"  # Reemplaza con tu chat ID real
    
    print("--- ORUS SISTEMA DE VIGILANCIA ONLINE ---")
    
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