import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackContext, ConversationHandler, filters
from fpdf import FPDF

# Configurar el bot
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "7163814190:AAGzhkR3H3SLBQc4LF4Zxi3J4_RnKd26u1M")  # Usa tu propio token
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")

# Etapas del flujo de conversación
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

# Función de inicio de la conversación
async def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("¡Bienvenido a Generador de Facturas! Vamos a generar una factura. Por favor, dime el nombre del cliente.")
    datos_usuarios[update.message.chat_id] = {"cliente": {}, "productos": []}
    return CLIENTE

# Solicita el nombre del cliente
async def cliente_nombre(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    datos_usuarios[chat_id]["cliente"]["nombre"] = update.message.text
    update.message.reply_text("¿Cuál es la dirección del cliente?")
    return CLIENTE

# Solicita la dirección del cliente
async def cliente_direccion(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    datos_usuarios[chat_id]["cliente"]["direccion"] = update.message.text
    update.message.reply_text("Dime el nombre del primer producto.")
    return PRODUCTOS

# Agrega un producto a la factura
async def agregar_producto(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    producto = {"nombre": update.message.text}
    datos_usuarios[chat_id]["productos"].append(producto)
    update.message.reply_text("¿Cuántas unidades?")
    return MAS_PRODUCTOS

# Agrega la cantidad del producto
async def agregar_cantidad(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    producto_actual = datos_usuarios[chat_id]["productos"][-1]
    producto_actual["cantidad"] = int(update.message.text)
    update.message.reply_text("¿Cuál es el precio unitario?")
    return MAS_PRODUCTOS

# Agrega el precio del producto y calcula el subtotal
async def agregar_precio(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    producto_actual = datos_usuarios[chat_id]["productos"][-1]
    producto_actual["precio"] = float(update.message.text)
    producto_actual["subtotal"] = producto_actual["cantidad"] * producto_actual["precio"]
    update.message.reply_text("¿Deseas agregar otro producto? (sí/no)")
    return CONFIRMAR

# Confirma si se deben agregar más productos o no
async def confirmar(update: Update, context: CallbackContext) -> int:
    if update.message.text.lower() == "sí":
        update.message.reply_text("Dime el nombre del siguiente producto.")
        return PRODUCTOS
    else:
        chat_id = update.message.chat_id
        await generar_factura(update, chat_id)
        return ConversationHandler.END

# Genera la factura y la envía al usuario
async def generar_factura(update: Update, chat_id: int):
    datos = datos_usuarios[chat_id]
    cliente = datos["cliente"]
    productos = datos["productos"]
    total = sum(p["subtotal"] for p in productos)

    # Crear la factura en PDF
    factura = Factura()
    factura.add_page()
    factura.agregar_cliente(cliente)
    factura.agregar_productos(productos)
    factura.agregar_total(total)

    # Guardar la factura en un archivo
    nombre_archivo = f"factura_{chat_id}.pdf"
    factura.output(nombre_archivo)

    # Enviar la factura como archivo al usuario
    with open(nombre_archivo, "rb") as archivo:
        await update.message.reply_document(archivo)
    await update.message.reply_text("¡Factura generada con éxito!")

# Función para cancelar el proceso
async def cancelar(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Proceso cancelado. ¡Hasta luego!")
    return ConversationHandler.END

# Función principal
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Configuración del flujo de conversación
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CLIENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cliente_nombre)],
            PRODUCTOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, agregar_producto)],
            MAS_PRODUCTOS: [
                MessageHandler(filters.regex(r'^\d+$'), agregar_cantidad),
                MessageHandler(filters.regex(r'^\d+(\.\d+)?$'), agregar_precio),
            ],
            CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    application.add_handler(conv_handler)
    application.run_polling()


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
