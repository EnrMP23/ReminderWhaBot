from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz

app = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.start()

# Almacenar recordatorios
recordatorios = {}

def enviar_notificacion(usuario, mensaje):
    print(f"Notificación enviada a {usuario}: {mensaje}")  # Simulación
    # Aquí puedes integrar un envío real a través de Twilio o WhatsApp

@app.route('/webhook', methods=['POST'])
def webhook():
    global recordatorios
    data = request.form
    usuario = data.get('From')
    mensaje = data.get('Body').strip().lower()
    
    response = MessagingResponse()
    reply = response.message()
    
    if mensaje.startswith("recordar"):
        try:
            partes = mensaje.split(" ", 2)
            fecha_hora = partes[1]
            texto_recordatorio = partes[2]
            
            fecha_hora_obj = datetime.strptime(fecha_hora, '%Y-%m-%d %H:%M')
            if usuario not in recordatorios:
                recordatorios[usuario] = []
            
            recordatorios[usuario].append((fecha_hora_obj, texto_recordatorio))
            scheduler.add_job(
                enviar_notificacion,
                'date',
                run_date=fecha_hora_obj,
                args=[usuario, texto_recordatorio]
            )
            
            reply.body("✅ Recordatorio agregado exitosamente.")
        except Exception as e:
            reply.body("❌ Error: Asegúrate de enviar el mensaje como 'recordar AAAA-MM-DD HH:MM mensaje'.")
    else:
        reply.body("🤖 Comando no reconocido. Usa 'recordar AAAA-MM-DD HH:MM mensaje' para crear un recordatorio.")
    
    return str(response)

if __name__ == '__main__':
    app.run(debug=True)
