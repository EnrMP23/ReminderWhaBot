import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from fpdf import FPDF
import qrcode

# Variables de configuración
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "7163814190:AAGzhkR3H3SLBQc4LF4Zxi3J4_RnKd26u1M")  # Reemplaza con tu token real
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")  # URL pública de tu webhook

# Clase personalizada para la factura
class Factura(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 8, "Factura CFDI", 0, 1, "C")
        self.set_font("Arial", "", 10)
        self.cell(0, 5, "RFC Emisor: MAPE002823JV6", 0, 1)
        self.cell(0, 5, "Nombre Emisor: ENRIQUE MAYNEZ PEREZ", 0, 1)
        self.cell(0, 5, "Dirección: AVENIDA PLAN DE IGUALA", 0, 1)
        self.ln(5)

    def agregar_datos_cliente(self, cliente):
        self.set_font("Arial", "B", 10)
        self.cell(0, 5, "Datos del Cliente", 0, 1)
        self.set_font("Arial", "", 9)
        self.cell(0, 5, f"Nombre: {cliente['nombre']}", 0, 1)
        self.cell(0, 5, f"RFC: {cliente['rfc']}", 0, 1)
        self.cell(0, 5, f"Dirección: {cliente['direccion']}", 0, 1)
        self.ln(5)

    def agregar_productos(self, productos):
        self.set_font("Arial", "B", 9)
        self.cell(30, 8, "Clave Prod.", 1)
        self.cell(60, 8, "Descripción", 1)
        self.cell(20, 8, "Cantidad", 1)
        self.cell(20, 8, "Unidad", 1)
        self.cell(30, 8, "Precio Unit.", 1)
        self.cell(30, 8, "Importe", 1)
        self.ln()
        self.set_font("Arial", "", 9)
        for producto in productos:
            self.cell(30, 8, producto["clave"], 1)
            self.cell(60, 8, producto["descripcion"], 1)
            self.cell(20, 8, str(producto["cantidad"]), 1)
            self.cell(20, 8, producto["unidad"], 1)
            self.cell(30, 8, f"${producto['precio_unitario']:.2f}", 1)
            self.cell(30, 8, f"${producto['importe']:.2f}", 1)
            self.ln()

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Por favor envía los datos del cliente: Nombre, RFC, Dirección"
    )

# Manejo de datos del cliente
async def handle_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        datos = update.message.text.split(",")
        context.user_data["cliente"] = {
            "nombre": datos[0].strip(),
            "rfc": datos[1].strip(),
            "direccion": datos[2].strip()
        }
        context.user_data["productos"] = []
        await update.message.reply_text(
            "Datos recibidos. Ahora envía productos en formato: Clave, Descripción, Cantidad, Unidad, Precio Unitario"
        )
    except IndexError:
        await update.message.reply_text("Formato incorrecto. Intenta nuevamente.")

# Manejo de productos
async def handle_producto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        datos = update.message.text.split(",")
        producto = {
            "clave": datos[0].strip(),
            "descripcion": datos[1].strip(),
            "cantidad": int(datos[2].strip()),
            "unidad": datos[3].strip(),
            "precio_unitario": float(datos[4].strip()),
            "importe": int(datos[2].strip()) * float(datos[4].strip()),
        }
        context.user_data["productos"].append(producto)
        await update.message.reply_text(
            "Producto añadido. Envía más productos o escribe /generar para crear la factura."
        )
    except (IndexError, ValueError):
        await update.message.reply_text("Formato inválido. Asegúrate de enviar los datos correctamente.")

# Generar factura
async def generar_factura(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cliente = context.user_data.get("cliente")
    productos = context.user_data.get("productos")

    if not cliente or not productos:
        await update.message.reply_text("Por favor, envía los datos del cliente y al menos un producto.")
        return

    # Calcular totales
    subtotal = sum(p["importe"] for p in productos)
    iva = subtotal * 0.16
    total = subtotal + iva

    # Crear la factura PDF
    factura = Factura()
    factura.add_page()
    factura.agregar_datos_cliente(cliente)
    factura.agregar_productos(productos)
    factura.set_font("Arial", "B", 10)
    factura.cell(160, 8, "Subtotal", 0, 0, "R")
    factura.cell(30, 8, f"${subtotal:.2f}", 1, 1, "R")
    factura.cell(160, 8, "IVA 16%", 0, 0, "R")
    factura.cell(30, 8, f"${iva:.2f}", 1, 1, "R")
    factura.cell(160, 8, "Total", 0, 0, "R")
    factura.cell(30, 8, f"${total:.2f}", 1, 1, "R")

    # Guardar PDF
    pdf_filename = "factura.pdf"
    factura.output(pdf_filename)

    # Enviar PDF al usuario
    with open(pdf_filename, "rb") as pdf_file:
        await update.message.reply_document(pdf_file)

    # Limpiar datos del usuario
    context.user_data.clear()

# Configurar y ejecutar el webhook
def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cliente))
    application.add_handler(CommandHandler("generar", generar_factura))

    # Configurar el webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=8443,  # Puerto HTTPS
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

    print("Bot funcionando con Webhook")

if __name__ == "__main__":
    main()
