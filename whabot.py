import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, ConversationHandler, filters
from fpdf import FPDF

# Configurar el bot
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "7163814190:AAGzhkR3H3SLBQc4LF4Zxi3J4_RnKd26u1M")  # Usa tu propio token
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")  # URL de tu webhook en Render

# Etapas del flujo de conversación
CLIENTE, CLIENTE_DIRECCION, CLIENTE_RFC, PRODUCTOS, CANTIDAD, PRECIO, CONFIRMAR = range(7)

# Diccionario para guardar los datos fiscales
DATOS_FISCALES_EMISOR = {
    "nombre": "ENRIQUE MAYNEZ PEREZ",  # Nombre de la empresa
    "rfc": "MAPE020823JV6",  # Tu RFC
    "domicilio": "AVENIDA PLAN DE IGUALA 269, HERMOSILLO, SONORA, MÉXICO",  # Tu domicilio fiscal
    "regimen_fiscal": "INGRESOS ASIMILADOS A SALARIOS",  # Tu régimen fiscal
    "correo": "enrmp2002@gmail.com",  # Tu correo electrónico
}

# Función de inicio de la conversación
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("¡Bienvenido a Generador de Facturas! Vamos a generar una factura. Por favor, dime el nombre del cliente.")
    datos_usuarios[update.message.chat_id] = {"cliente": {}, "productos": []}
    return CLIENTE

# Solicita el nombre del cliente
async def cliente_nombre(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    datos_usuarios[chat_id]["cliente"]["nombre"] = update.message.text
    await update.message.reply_text("¿Cuál es el RFC del cliente?")
    return CLIENTE_RFC  # Redirige a la solicitud del RFC del cliente

# Solicita el RFC del cliente
async def cliente_rfc(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    datos_usuarios[chat_id]["cliente"]["rfc"] = update.message.text
    await update.message.reply_text("¿Cuál es la dirección del cliente?")
    return CLIENTE_DIRECCION  # Redirige a la solicitud de dirección

# Solicita la dirección del cliente
async def cliente_direccion(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    datos_usuarios[chat_id]["cliente"]["direccion"] = update.message.text
    await update.message.reply_text("Dime el nombre del primer producto.")
    return PRODUCTOS  # Regresa a la etapa PRODUCTOS

# Agrega un producto a la factura
async def agregar_producto(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    producto = {"nombre": update.message.text}
    datos_usuarios[chat_id]["productos"].append(producto)
    await update.message.reply_text("¿Cuántas unidades?")
    return CANTIDAD

# Agrega la cantidad del producto
async def agregar_cantidad(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    producto_actual = datos_usuarios[chat_id]["productos"][-1]
    try:
        producto_actual["cantidad"] = int(update.message.text)
        await update.message.reply_text("¿Cuál es el precio unitario?")
        return PRECIO
    except ValueError:
        await update.message.reply_text("Por favor, ingresa un número válido para la cantidad.")
        return CANTIDAD

# Agrega el precio del producto y calcula el subtotal
async def agregar_precio(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    producto_actual = datos_usuarios[chat_id]["productos"][-1]
    try:
        producto_actual["precio"] = float(update.message.text)
        producto_actual["subtotal"] = producto_actual["cantidad"] * producto_actual["precio"]
        await update.message.reply_text("¿Deseas agregar otro producto? (sí/no)")
        return CONFIRMAR
    except ValueError:
        await update.message.reply_text("Por favor, ingresa un precio válido.")
        return PRECIO

# Confirma si se deben agregar más productos o no
async def confirmar(update: Update, context: CallbackContext) -> int:
    if update.message.text.lower() == "sí":
        await update.message.reply_text("Dime el nombre del siguiente producto.")
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
    
    # Agregar datos fiscales del emisor
    factura.set_font('Arial', 'B', 10)
    factura.cell(0, 10, f'Emisor: {DATOS_FISCALES_EMISOR["nombre"]}', 0, 1)
    factura.cell(0, 10, f'RFC: {DATOS_FISCALES_EMISOR["rfc"]}', 0, 1)
    factura.cell(0, 10, f'Domicilio: {DATOS_FISCALES_EMISOR["domicilio"]}', 0, 1)
    factura.cell(0, 10, f'Regimen Fiscal: {DATOS_FISCALES_EMISOR["regimen_fiscal"]}', 0, 1)
    
    # Agregar datos fiscales del receptor (cliente)
    factura.cell(0, 10, f'Cliente: {cliente["nombre"]}', 0, 1)
    factura.cell(0, 10, f'RFC: {cliente["rfc"]}', 0, 1)
    factura.cell(0, 10, f'Dirección: {cliente["direccion"]}', 0, 1)
    
    # Agregar productos
    factura.agregar_productos(productos)
    
    # Agregar total
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
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Configuración del flujo de conversación
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CLIENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cliente_nombre)],
            CLIENTE_RFC: [MessageHandler(filters.TEXT & ~filters.COMMAND, cliente_rfc)],  # Nueva etapa RFC
            CLIENTE_DIRECCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, cliente_direccion)],
            PRODUCTOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, agregar_producto)],
            CANTIDAD: [MessageHandler(filters.Regex(r'^\d+$'), agregar_cantidad)],  # Solo cantidad
            PRECIO: [MessageHandler(filters.Regex(r'^\d+(\.\d+)?$'), agregar_precio)],  # Solo precio
            CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    application.add_handler(conv_handler)

    # Configuración del Webhook
    application.run_webhook(
        listen="0.0.0.0",  # Escuchar en todas las interfaces de red
        port=8443,          # Puerto por defecto para webhook
        url_path="/webhook",  # Ruta del webhook
        webhook_url=WEBHOOK_URL  # URL completa del webhook
    )

    print("BOT FUNCIONANDO CORRECTAMENTE")

if __name__ == '__main__':
    main()
