from __future__ import annotations

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.services.allocation import (
    get_operational_status,
    get_people_list,
    rebalance_staff,
    record_absence,
    register_alert,
    reset_demo_data,
)

ABSENCE_NAME, ABSENCE_REASON = range(2)
ALERT_TEXT, ALERT_LOCATION = range(2)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ['/estado', '/reorganizar'],
        ['/ausencia', '/alerta'],
        ['/personas', '/reset_demo'],
    ],
    resize_keyboard=True,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        '🚑 Bot de coordinación SAMUR\n\n'
        'Comandos principales:\n'
        '/estado - ver cobertura actual\n'
        '/ausencia - informar una baja\n'
        '/alerta - registrar una incidencia tipo Ojo en Alerta\n'
        '/reorganizar - recalcular la dotación\n'
        '/personas - ver nombres cargados\n'
        '/reset_demo - restaurar los datos de prueba'
    )
    await update.message.reply_text(text, reply_markup=MAIN_KEYBOARD)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(get_operational_status(), reply_markup=MAIN_KEYBOARD)


async def people_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    people = get_people_list()
    await update.message.reply_text('👥 Personal cargado:\n' + '\n'.join(f'- {p}' for p in people))


async def rebalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = rebalance_staff()
    detail = '\n'.join(f'• {move}' for move in result.moves) if result.moves else '• Sin movimientos entre bases.'
    await update.message.reply_text(f'{result.summary}\n\n{detail}', reply_markup=MAIN_KEYBOARD)


async def reset_demo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(reset_demo_data(), reply_markup=MAIN_KEYBOARD)


async def absence_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Escribime el nombre completo de la persona ausente.',
        reply_markup=ReplyKeyboardRemove(),
    )
    return ABSENCE_NAME


async def absence_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['absence_name'] = update.message.text.strip()
    await update.message.reply_text('Indicá el motivo de la ausencia.')
    return ABSENCE_REASON


async def absence_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    full_name = context.user_data.get('absence_name', '').strip()
    reason = update.message.text.strip()
    user = update.effective_user.full_name if update.effective_user else 'telegram'
    result = record_absence(full_name=full_name, reason=reason, reported_by=user)
    await update.message.reply_text(result['message'], reply_markup=MAIN_KEYBOARD)
    context.user_data.clear()
    return ConversationHandler.END


async def alert_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Describí la alerta o incidencia operativa.',
        reply_markup=ReplyKeyboardRemove(),
    )
    return ALERT_TEXT


async def alert_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['alert_text'] = update.message.text.strip()
    await update.message.reply_text('Indicá ubicación o base afectada.')
    return ALERT_LOCATION


async def alert_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    description = context.user_data.get('alert_text', '').strip()
    location = update.message.text.strip()
    message = register_alert(description=description, location=location)
    await update.message.reply_text(message, reply_markup=MAIN_KEYBOARD)
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text('Operación cancelada.', reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END


def build_handlers() -> list:
    absence_conversation = ConversationHandler(
        entry_points=[CommandHandler('ausencia', absence_start)],
        states={
            ABSENCE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, absence_name)],
            ABSENCE_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, absence_reason)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    alert_conversation = ConversationHandler(
        entry_points=[CommandHandler('alerta', alert_start)],
        states={
            ALERT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, alert_text)],
            ALERT_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, alert_location)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    return [
        CommandHandler('start', start),
        CommandHandler('help', help_command),
        CommandHandler('estado', status_command),
        CommandHandler('personas', people_command),
        CommandHandler('reorganizar', rebalance_command),
        CommandHandler('reset_demo', reset_demo_command),
        absence_conversation,
        alert_conversation,
    ]
