"""
antidup_bot.py - Bot eliminador de duplicados para grupos de Telegram
=====================================================================
- Creado con BotFather (token oficial)
- Detecta duplicados: fotos, videos, audios, documentos, stickers
- Se agrega como admin al grupo y elimina automaticamente
- Listo para Railway.app (24/7)
"""

import hashlib
import logging
import os
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ===================== CONFIG =====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8117198557:AAFkHt53dxHUeHM_i02Nw-TY5ItvXvg0aEI")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("antidup")

# ===================== MEMORIA =====================
memoria: dict = {}
stats:   dict = {}

def obtener_memoria(chat_id):
    if chat_id not in memoria:
        memoria[chat_id] = set()
    return memoria[chat_id]

def obtener_stats(chat_id):
    if chat_id not in stats:
        stats[chat_id] = {"eliminados": 0, "procesados": 0, "nombre": str(chat_id)}
    return stats[chat_id]

def obtener_clave(message):
    try:
        if message.photo:
            return f"photo:{message.photo[-1].file_unique_id}"
        if message.video:
            return f"video:{message.video.file_unique_id}"
        if message.audio:
            return f"audio:{message.audio.file_unique_id}"
        if message.voice:
            return f"voice:{message.voice.file_unique_id}"
        if message.video_note:
            return f"videonote:{message.video_note.file_unique_id}"
        if message.document:
            return f"doc:{message.document.file_unique_id}"
        if message.sticker:
            return f"sticker:{message.sticker.file_unique_id}"
    except Exception as e:
        log.warning(f"Error obteniendo clave: {e}")
    return None

# ===================== HANDLER PRINCIPAL =====================
async def revisar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat    = update.effective_chat
    if not message or not chat:
        return
    if chat.type not in ("group", "supergroup"):
        return

    chat_id = chat.id
    mem     = obtener_memoria(chat_id)
    st      = obtener_stats(chat_id)
    st["nombre"]     = chat.title or str(chat_id)
    st["procesados"] += 1

    clave = obtener_clave(message)
    if clave is None:
        return

    if clave in mem:
        try:
            await message.delete()
            st["eliminados"] += 1
            ts = datetime.now().strftime("%H:%M:%S")
            log.info(f"[{ts}] ELIMINADO en '{st['nombre']}' | ID:{message.message_id} | {clave[:40]}")
        except Exception as e:
            log.warning(f"No pude eliminar ID:{message.message_id}: {e}")
            log.warning("Verifica que el bot sea admin con permiso 'Eliminar mensajes'")
    else:
        mem.add(clave)

# ===================== COMANDOS =====================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hola! Soy el bot antiduplicados.\n\n"
        "📋 Como usarme:\n"
        "1. Agrégame a tu grupo\n"
        "2. Hazme admin con permiso de Eliminar mensajes\n"
        "3. Listo, eliminaré duplicados automáticamente\n\n"
        "Comandos en el grupo:\n"
        "/stats - ver estadísticas\n"
        "/reset - limpiar memoria\n"
        "/ayuda - ayuda"
    )

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("Este comando es solo para grupos.")
        return
    st  = obtener_stats(chat.id)
    mem = obtener_memoria(chat.id)
    await update.message.reply_text(
        f"📊 Estadísticas AntiDup\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Grupo: {chat.title}\n"
        f"🗂 Archivos en memoria: {len(mem)}\n"
        f"✅ Mensajes procesados: {st['procesados']}\n"
        f"🗑 Duplicados eliminados: {st['eliminados']}"
    )

async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("Este comando es solo para grupos.")
        return
    try:
        admins    = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [a.user.id for a in admins]
        if update.effective_user.id not in admin_ids:
            await update.message.reply_text("Solo los admins pueden hacer esto.")
            return
    except Exception:
        pass
    antes = len(obtener_memoria(chat.id))
    memoria[chat.id] = set()
    await update.message.reply_text(
        f"✅ Memoria limpiada. {antes} registros borrados.\n"
        f"Ahora detecto duplicados desde cero."
    )

async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AntiDup Bot\n\n"
        "Elimino duplicados automáticamente en tu grupo.\n\n"
        "Comandos:\n"
        "/stats - estadísticas\n"
        "/reset - limpiar memoria (solo admins)\n"
        "/ayuda - esta ayuda\n\n"
        "Detecto duplicados de:\n"
        "📷 Fotos | 🎬 Videos | 🎵 Audios\n"
        "📎 Documentos | 🎭 Stickers"
    )

# ===================== MAIN =====================
def main():
    log.info("Iniciando AntiDup Bot...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("stats",  cmd_stats))
    app.add_handler(CommandHandler("reset",  cmd_reset))
    app.add_handler(CommandHandler("ayuda",  cmd_ayuda))
    app.add_handler(MessageHandler(
        filters.ALL & filters.ChatType.GROUPS,
        revisar_mensaje
    ))
    log.info("Bot activo. Esperando mensajes...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
