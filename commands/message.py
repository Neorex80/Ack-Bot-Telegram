from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from utils.permissions import is_user_admin

async def purge_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❗ Please reply to a message to start purging from.")
        return

    chat_id = update.effective_chat.id
    start_message_id = update.message.reply_to_message.message_id
    end_message_id = update.message.message_id
    deleted_count = 0

    try:
        for msg_id in range(start_message_id, end_message_id + 1):
            try:
                await context.bot.delete_message(chat_id, msg_id)
                deleted_count += 1
            except:
                continue

        confirmation = await context.bot.send_message(
            chat_id=chat_id,
            text=f"🗑️ Purged {deleted_count} messages."
        )

        context.job_queue.run_once(
            delete_message_callback,
            5,
            data={'chat_id': chat_id, 'message_id': confirmation.message_id}
        )

    except Exception as e:
        await update.message.reply_text(f"Failed to purge messages: {e}")

async def delete_message_callback(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    try:
        await context.bot.delete_message(job_data['chat_id'], job_data['message_id'])
    except:
        pass

# ---------------- Pin Command ----------------
async def pin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❗ Please reply to the message you want to pin.")
        return

    chat_id = update.effective_chat.id
    msg_id = update.message.reply_to_message.message_id
    notify = not (context.args and context.args[0].lower() in ['silent', 'quiet', 's', 'q'])

    try:
        await context.bot.pin_chat_message(chat_id, msg_id, disable_notification=not notify)
        await update.message.reply_text("📌 Message pinned successfully!")
    except Exception as e:
        await update.message.reply_text(f"Failed to pin message: {e}")

# ---------------- Unpin Command ----------------
async def unpin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    chat_id = update.effective_chat.id

    try:
        if update.message.reply_to_message:
            msg_id = update.message.reply_to_message.message_id
            await context.bot.unpin_chat_message(chat_id, msg_id)
        else:
            await context.bot.unpin_chat_message(chat_id)

        await update.message.reply_text("✅ Message unpinned successfully!")
    except Exception as e:
        await update.message.reply_text(f"Failed to unpin message: {e}")

# ---------------- Unpin All Command ----------------
async def unpinall_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    keyboard = [
        [InlineKeyboardButton("✅ Yes", callback_data="unpinall_yes"),
         InlineKeyboardButton("❌ No", callback_data="unpinall_no")]
    ]

    await update.message.reply_text(
        "Are you sure you want to unpin ALL pinned messages in this chat?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def unpinall_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not await is_user_admin(update, context):
        await query.edit_message_text("❌ You don't have permission to use this command.")
        return

    if query.data.endswith("yes"):
        try:
            await context.bot.unpin_all_chat_messages(query.message.chat.id)
            await query.edit_message_text("📌 All messages have been unpinned!")
        except Exception as e:
            await query.edit_message_text(f"Failed to unpin all messages: {e}")
    else:
        await query.edit_message_text("Operation cancelled.")

# ---------------- Register Handlers ----------------
def register_message_handler(app):
    app.add_handler(CommandHandler("purge", purge_command))
    app.add_handler(CommandHandler("pin", pin_command))
    app.add_handler(CommandHandler("unpin", unpin_command))
    app.add_handler(CommandHandler("unpinall", unpinall_command))
    app.add_handler(CallbackQueryHandler(unpinall_callback, pattern=r"^unpinall_(yes|no)$"))
