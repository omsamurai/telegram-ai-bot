import os
import logging
import requests
import asyncio
import re
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("HYPERBOLIC_API")
BASE_URL = os.getenv("AI_BASE_URL")

# Premium emojis
EMOJI = {
    "exited": "5850583766048706194",   # 🤩
    "eyes": "5877296091807878935",     # 👀
    "running": "5989913411369045839",  # 🏃
    "hurrey": "5987781295114030903",   # 🎉
    "question_mark": "5956290878367599999",  # ❕
    "nice": "5848061692533018037",     # 😍
    "star": "5850194835285217190",     # ✨
    "cool": "5987736155007750325",     # 😎
    "ghost": "5987594979432731998"     # 👻
}

async def safe_reply(update: Update, text: str, **kwargs) -> Message:
    if update.message:
        return await update.message.reply_text(
            text,
            reply_to_message_id=update.message.message_id,
            **kwargs
        )
    else:
        return await update.effective_chat.send_message(text, **kwargs)

def format_ai_response(text: str) -> str:
    """Convert Markdown-style formatting into HTML tags."""
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)   # bold
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)       # italics
    text = re.sub(r"`(.*?)`", r"<code>\1</code>", text)   # inline code
    text = re.sub(r"^- (.*?)$", r"• \1", text, flags=re.MULTILINE)  # bullet lists
    return text

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = f'<tg-emoji emoji-id="{EMOJI["exited"]}">🤩</tg-emoji> Welcome!'
    await safe_reply(update, welcome_text, parse_mode="HTML")

    helper_text = (
        f'<tg-emoji emoji-id="{EMOJI["eyes"]}">👀</tg-emoji> '
        'Use <code>/ai &lt;message&gt;</code> to chat with me'
    )
    await safe_reply(update, helper_text, parse_mode="HTML")

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("👨🏻‍💻 Developer", url="https://t.me/unseen_crafts"),
            InlineKeyboardButton("👻 GitHub Repo", url="https://github.com/omsamurai/telegram-ai-bot")
        ],
        [
            InlineKeyboardButton("🤖 Hyperbolic", url="https://hyperbolic.xyz")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    help_text = (
        f'<tg-emoji emoji-id="{EMOJI["nice"]}">😍</tg-emoji> <b>Telegram AI Bot</b>\n\n'
        f'<tg-emoji emoji-id="{EMOJI["star"]}">✨</tg-emoji> <b>Commands:</b>\n'
        '/start - Welcome\n'
        '/ai &lt;message&gt; - Ask AI\n'
        '/help - Bot info\n\n'
        f'<tg-emoji emoji-id="{EMOJI["cool"]}">😎</tg-emoji> <b>Powered by -</b> @unseen_crafts'
    )
    await safe_reply(update, help_text, reply_markup=reply_markup, parse_mode="HTML")

# /ai command
async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args and not update.message.reply_to_message:
        guide_txt = (
            f'<tg-emoji emoji-id="{EMOJI["question_mark"]}">❕</tg-emoji> '
            '<b>Ex:</b> <code>/ai best ai model</code>'
        )
        await safe_reply(update, guide_txt, parse_mode="HTML")
        return

    user_message = " ".join(context.args) if context.args else update.message.reply_to_message.text

    searching_msg = await safe_reply(
        update,
        f'<tg-emoji emoji-id="{EMOJI["running"]}">🏃</tg-emoji> Searching...',
        parse_mode="HTML"
    )

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        data = {
            "messages": [{"role": "user", "content": user_message}],
            "model": "moonshotai/Kimi-K2-Instruct",
            "max_tokens": 512,
            "temperature": 0.1,
            "top_p": 0.9
        }

        response = requests.post(BASE_URL, headers=headers, json=data)
        result = response.json()

        await asyncio.sleep(2)

        if "choices" in result and len(result["choices"]) > 0:
            raw_answer = result["choices"][0]["message"]["content"]
            answer = format_ai_response(raw_answer)

            await searching_msg.edit_text(
                f'<tg-emoji emoji-id="{EMOJI["hurrey"]}">🎉</tg-emoji> Found result!',
                parse_mode="HTML"
            )
            await asyncio.sleep(1)
            await searching_msg.delete()

            if update.message.reply_to_message:
                await update.message.reply_to_message.reply_text(answer, parse_mode="HTML")
            else:
                await update.message.reply_text(answer, parse_mode="HTML")

        elif "error" in result:
            await searching_msg.edit_text(
                f'<tg-emoji emoji-id="{EMOJI["ghost"]}">👻</tg-emoji> <b>API Error:</b> {result["error"]["message"]}',
                parse_mode="HTML"
            )
            await asyncio.sleep(2)
            await searching_msg.delete()
        else:
            await searching_msg.edit_text(
                f'<tg-emoji emoji-id="{EMOJI["ghost"]}">👻</tg-emoji> <b>Unexpected API response format.</b>',
                parse_mode="HTML"
            )
            await asyncio.sleep(2)
            await searching_msg.delete()

    except Exception as e:
        logging.error(f"API error: {e}")
        await searching_msg.edit_text(
            f'<tg-emoji emoji-id="{EMOJI["ghost"]}">👻</tg-emoji> <b>Sorry, something went wrong with the AI API.</b>',
            parse_mode="HTML"
        )
        await asyncio.sleep(2)
        await searching_msg.delete()

# Main
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ai", ai_command))
    app.run_polling()

if __name__ == "__main__":
    main()
