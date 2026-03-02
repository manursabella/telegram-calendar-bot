import re
import io
import logging
from datetime import datetime, timedelta

import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from PIL import Image
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import dateparser

from config import TELEGRAM_BOT_TOKEN
import google_calendar

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

(ASK_TITLE, ASK_START_DATE, ASK_START_TIME, ASK_END_TIME, ASK_RECURRENCE, ASK_END_RECURRENCE) = range(6)

user_events = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu asistente de calendario.\n\n"
        "Puedo crear eventos en Google Calendar.\n\n"
        "Usa /new para crear un nuevo evento\n"
        "Usa /events para ver tus próximos eventos\n"
        "Usa /cancel para cancelar la creación"
    )

async def new_event_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Vamos a crear un evento. ¿Cómo se llama?")
    return ASK_TITLE

async def ask_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_events[user_id] = {'title': update.message.text}
    await update.message.reply_text("¿Desde qué fecha? (ej: 15/03/2026 o \"lunes\" o \"mañana\")")
    return ASK_START_DATE

async def ask_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()
    
    parsed_date = parse_date(text)
    if not parsed_date:
        await update.message.reply_text("No entendí la fecha. Intenta de nuevo (ej: 15/03/2026)")
        return ASK_START_DATE
    
    user_events[user_id]['start_date'] = parsed_date
    await update.message.reply_text("¿A qué hora empieza? (ej: 18:30)")
    return ASK_START_TIME

async def ask_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()
    
    time_info = parse_time(text)
    if not time_info:
        await update.message.reply_text("No entendí la hora. Intenta de nuevo (ej: 18:30)")
        return ASK_START_TIME
    
    user_events[user_id]['start_time'] = time_info
    await update.message.reply_text("¿A qué hora termina? (ej: 21:40)")
    return ASK_END_TIME

async def ask_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()
    
    time_info = parse_time(text)
    if not time_info:
        await update.message.reply_text("No entendí la hora. Intenta de nuevo (ej: 21:40)")
        return ASK_END_TIME
    
    user_events[user_id]['end_time'] = time_info
    
    await update.message.reply_text(
        "¿Se repite? Responde:\n"
        "- 'no' o 'una vez'\n"
        "- 'todos los lunes' (o martes, miércoles, etc.)\n"
        "- 'diario'\n"
        "- 'semanal'"
    )
    return ASK_RECURRENCE

async def ask_recurrence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()
    
    recurrence = None
    
    if 'no' in text or 'una vez' in text or 'vez' in text:
        recurrence = None
    elif 'lunes' in text:
        recurrence = 'RRULE:FREQ=WEEKLY;BYDAY=MO'
    elif 'martes' in text:
        recurrence = 'RRULE:FREQ=WEEKLY;BYDAY=TU'
    elif 'miércoles' in text or 'miercoles' in text:
        recurrence = 'RRULE:FREQ=WEEKLY;BYDAY=WE'
    elif 'jueves' in text:
        recurrence = 'RRULE:FREQ=WEEKLY;BYDAY=TH'
    elif 'viernes' in text:
        recurrence = 'RRULE:FREQ=WEEKLY;BYDAY=FR'
    elif 'sábado' in text or 'sabado' in text:
        recurrence = 'RRULE:FREQ=WEEKLY;BYDAY=SA'
    elif 'domingo' in text:
        recurrence = 'RRULE:FREQ=WEEKLY;BYDAY=SU'
    elif 'diario' in text or 'todos los días' in text or 'todos los dias' in text:
        recurrence = 'RRULE:FREQ=DAILY'
    elif 'semanal' in text:
        recurrence = 'RRULE:FREQ=WEEKLY'
    
    if recurrence:
        user_events[user_id]['recurrence_rule'] = recurrence
        await update.message.reply_text("¿Hasta qué fecha se repite? (ej: 11/05/2026 o 'mayo' o 'nunca')")
        return ASK_END_RECURRENCE
    
    return await create_event(update, context, user_id, None)

async def ask_end_recurrence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()
    
    recurrence = user_events[user_id].get('recurrence_rule')
    
    if 'nunca' in text or 'no' in text:
        end_date = None
    else:
        end_date = parse_date(text)
    
    if recurrence and end_date:
        recurrence += f';UNTIL={end_date.strftime("%Y%m%d")}'
    
    return await create_event(update, context, user_id, recurrence)

async def create_event(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, recurrence: str):
    event = user_events.get(user_id)
    if not event:
        await update.message.reply_text("Error: no encontré el evento. Usa /new para empezar de nuevo.")
        return ConversationHandler.END
    
    start_date = event['start_date']
    start_time = event['start_time']
    end_time = event['end_time']
    
    start_datetime = start_date.replace(hour=start_time[0], minute=start_time[1], second=0, microsecond=0)
    end_datetime = start_date.replace(hour=end_time[0], minute=end_time[1], second=0, microsecond=0)
    
    if end_datetime <= start_datetime:
        end_datetime += timedelta(days=1)
    
    title = event['title']
    
    success, result = google_calendar.create_event(
        summary=title,
        description="Creado desde Telegram Bot",
        start_time=start_datetime.isoformat(),
        end_time=end_datetime.isoformat(),
        recurrence_rule=recurrence
    )
    
    if success:
        recurrence_msg = ""
        if recurrence:
            if 'WEEKLY' in recurrence:
                recurrence_msg = "\n🔄 Se repite semanalmente"
            elif 'DAILY' in recurrence:
                recurrence_msg = "\n🔄 Se repite diariamente"
        
        await update.message.reply_text(
            f"✅ ¡Evento creado!\n\n"
            f"📌 {title}\n"
            f"📅 {start_datetime.strftime('%d/%m/%Y')}\n"
            f"🕐 {start_datetime.strftime('%H:%M')} - {end_datetime.strftime('%H:%M')}{recurrence_msg}\n\n"
            f"{result}"
        )
    else:
        await update.message.reply_text(f"❌ Error: {result}")
    
    if user_id in user_events:
        del user_events[user_id]
    
    return ConversationHandler.END

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_events:
        del user_events[user_id]
    await update.message.reply_text("Creación de evento cancelada.")
    return ConversationHandler.END

def parse_date(text: str):
    text = text.lower()
    
    if 'hoy' in text:
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif 'mañana' in text or 'manana' in text:
        return (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif 'lunes' in text:
        return next_weekday(0)
    elif 'martes' in text:
        return next_weekday(1)
    elif 'miércoles' in text or 'miercoles' in text:
        return next_weekday(2)
    elif 'jueves' in text:
        return next_weekday(3)
    elif 'viernes' in text:
        return next_weekday(4)
    elif 'sábado' in text or 'sabado' in text:
        return next_weekday(5)
    elif 'domingo' in text:
        return next_weekday(6)
    
    formats = ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).replace(hour=0, minute=0, second=0, microsecond=0)
        except:
            pass
    
    parsed = dateparser.parse(text, languages=['es'])
    if parsed:
        return parsed.replace(hour=0, minute=0, second=0, microsecond=0)
    
    return None

def next_weekday(weekday: int):
    now = datetime.now()
    days_ahead = weekday - now.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return (now + timedelta(days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)

def parse_time(text: str):
    text = text.lower()
    
    match = re.search(r'(\d{1,2})[:.](\d{2})', text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        
        if 'pm' in text and hour < 12:
            hour += 12
        elif 'am' in text and hour == 12:
            hour = 0
        
        return (hour, minute)
    
    match = re.search(r'(\d{1,2})\s*(am|pm)?', text)
    if match:
        hour = int(match.group(1))
        minute = 0
        
        if 'pm' in text and hour < 12:
            hour += 12
        elif 'am' in text and hour == 12:
            hour = 0
        
        return (hour, minute)
    
    return None

async def list_events_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cargando eventos...")
    
    events = google_calendar.list_events(5)
    
    if not events:
        await update.message.reply_text("No hay eventos próximos.")
        return
    
    message = "📅 Tus próximos eventos:\n\n"
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        summary = event.get('summary', 'Sin título')
        
        if 'T' in start:
            dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            date_str = dt.strftime("%d/%m/%Y %H:%M")
        else:
            date_str = start
        
        message += f"• {summary}\n  {date_str}\n\n"
    
    await update.message.reply_text(message)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Usa /new para crear un evento o /events para ver eventos.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Usa /new para crear un evento primero.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text("Ocurrió un error. Por favor intenta de nuevo.")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("new", new_event_command)],
        states={
            ASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_title)],
            ASK_START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_start_date)],
            ASK_START_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_start_time)],
            ASK_END_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_end_time)],
            ASK_RECURRENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_recurrence)],
            ASK_END_RECURRENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_end_recurrence)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("events", list_events_command))
    application.add_handler(CommandHandler("help", start_command))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    application.add_error_handler(error_handler)
    
    logger.info("Bot iniciado...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
