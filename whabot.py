from telegram import Update, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, ConversationHandler
from telegram import ext
from fpdf import FPDF
import io
import os

# Configurar el bot
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "7163814190:AAGzhkR3H3SLBQc4LF4Zxi3J4_RnKd26u1M")  # Usar una variable de entorno para el token
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")

# Etapas del flujo
CLIENTE, PRODUCTOS, MAS_PRODUCTOS, CONFIRMAR = range(4)

# Diccionario para guardar datos temporales de cada usuario
datos_usuarios = {}

# Clase para generar la factura
class Factura(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Décima Avenida - Factura', 0, 1, 'C')

    def agregar_cliente(self, cliente):
        self.set_font('Arial', '', 10)
        self.cell(0, 10, f'Cliente: {cliente["nombre"]}', 0, 1)
        self.cell(0, 10, f'Dirección: {cliente["direccion"]}', 0, 1)

    def agregar_productos(self, productos):
        self.set_font('Arial', 'B', 10)
        self.cell(40, 10, 'Producto', 1)
        self.cell(30, 10, 'Cantidad', 1)
        self.cell(30, 10, 'Precio Unitario', 1)
        self.cell(30, 10, 'Subtotal', 1)
        self.ln()
        self.set_font('Arial', '', 10)
        for p in productos:
            self.cell(40, 10, p['nombre'], 1)
            self.cell(30, 10, str(p['cantidad']), 1)
            self.cell(30, 10, f'${p["precio"]:.2f}', 1)
            self.cell(30, 10, f'${p["subtotal"]:.2f}', 1)
            self.ln()

    def agregar_total(self, total):
        self.set_font('Arial', 'B', 10)
        self.cell(100, 10, '', 0)
        self.cell(30, 10, 'Total', 1)
        self.cell(30, 10, f'${total:.2f}', 1)

# Inicia el flujo
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("¡Bienvenido a Generador de Facturas! Vamos a generar una factura. Por favor, dime el nombre del cliente.")
    datos_usuarios[update.message.chat_id] = {"cliente": {}, "productos": []}
    return CLIENTE

# Solicita el nombre del cliente
def cliente_nombre(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    datos_usuarios[chat_id]["cliente"]["nombre"] = update.message.text
    update.message.reply_text("¿Cuál es la dirección del cliente?")
    return CLIENTE

# Solicita la dirección del cliente
def cliente_direccion(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    datos_usuarios[chat_id]["cliente"]["direccion"] = update.message.text
    update.message.reply_text("Dime el nombre del primer producto.")
    return PRODUCTOS

# Agrega productos
def agregar_producto(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    producto = {"nombre": update.message.text}
    datos_usuarios[chat_id]["productos"].append(producto)
    update.message.reply_text("¿Cuántas unidades?")
    return MAS_PRODUCTOS

# Agrega cantidad y precio
def agregar_cantidad(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    producto_actual = datos_usuarios[chat_id]["productos"][-1]
    producto_actual["cantidad"] = int(update.message.text)
    update.message.reply_text("¿Cuál es el precio unitario?")
    return MAS_PRODUCTOS

# Calcula subtotal y pregunta si agregar más productos
def agregar_precio(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    producto_actual = datos_usuarios[chat_id]["productos"][-1]
    producto_actual["precio"] = float(update.message.text)
    producto_actual["subtotal"] = producto_actual["cantidad"] * producto_actual["precio"]
    update.message.reply_text("¿Deseas agregar otro producto? (sí/no)")
    return CONFIRMAR

# Confirmar más productos o finalizar
def confirmar(update: Update, context: CallbackContext) -> int:
    if update.message.text.lower() == "sí":
        update.message.reply_text("Dime el nombre del siguiente producto.")
        return PRODUCTOS
    else:
        chat_id = update.message.chat_id
        generar_factura(update, chat_id)
        return ConversationHandler.END

# Generar factura
def generar_factura(update: Update, chat_id: int):
    datos = datos_usuarios[chat_id]
    cliente = datos["cliente"]
    productos = datos["productos"]
    total = sum(p["subtotal"] for p in productos)

    # Crear factura
    factura = Factura()
    factura.add_page()
    factura.agregar_cliente(cliente)
    factura.agregar_productos(productos)
    factura.agregar_total(total)

    # Guardar factura
    nombre_archivo = f"factura_{chat_id}.pdf"
    factura.output(nombre_archivo)

    # Enviar factura
    with open(nombre_archivo, "rb") as archivo:
        context = CallbackContext(update.effective_chat.id)
        update.message.reply_document(archivo)
    update.message.reply_text("¡Factura generada con éxito!")

# Cancelar el flujo
def cancelar(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Proceso cancelado. ¡Hasta luego!")
    return ConversationHandler.END

# Configuración del bot
def main():
    TOKEN = TELEGRAM_TOKEN
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # Configurar flujo de conversación
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CLIENTE: [MessageHandler(ext.filters.TEXT & ~ext.filters.COMMAND, cliente_nombre)
],
            PRODUCTOS: [MessageHandler(ext.Filters.text & ~Filters.command, agregar_producto)],
            MAS_PRODUCTOS: [
                MessageHandler(ext.Filters.regex(r'^\d+$'), agregar_cantidad),
                MessageHandler(ext.Filters.regex(r'^\d+(\.\d+)?$'), agregar_precio),
            ],
            CONFIRMAR: [MessageHandler(ext.Filters.text & ~Filters.command, confirmar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancelar", cancelar))
    application.run_webhook(
        listen="0.0.0.0",
        port=8443,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

    print("BOT FUNCIONANDO CORRECTAMENTE")
