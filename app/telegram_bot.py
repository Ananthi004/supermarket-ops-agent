import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =========================================================
# PROJECT PATH
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

# Load venv/.env
load_dotenv(PROJECT_ROOT / "venv" / ".env")

# Load project .env if present
load_dotenv(PROJECT_ROOT / ".env")


# =========================================================
# IMPORT AGENT
# =========================================================

from gemini_agent.agent import root_agent


# =========================================================
# TELEGRAM TOKEN
# =========================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN was not found in .env or venv/.env"
    )


# =========================================================
# ADK CONFIGURATION
# =========================================================

APP_NAME = "supermarket_ops_agent"


session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


# =========================================================
# FILE DIRECTORIES
# =========================================================

INVOICE_DIR = PROJECT_ROOT / "data" / "invoices"
REPORT_DIR = PROJECT_ROOT / "data" / "analysis"

INVOICE_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# ASK AGENT
# =========================================================

async def ask_agent(user_id: str, message: str) -> str:
    """
    Send a user message to the Gemini ADK agent
    and return the final text response.
    """

    session_id = f"telegram_{user_id}"

    # -----------------------------------------------------
    # Create session if it does not already exist
    # -----------------------------------------------------

    try:
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )
    except Exception:
        # Session probably already exists.
        pass

    # -----------------------------------------------------
    # Create user message
    # -----------------------------------------------------

    content = types.Content(
        role="user",
        parts=[
            types.Part(
                text=message
            )
        ],
    )

    # -----------------------------------------------------
    # Run agent
    # -----------------------------------------------------

    final_response = ""

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):

            if event.is_final_response():

                if event.content and event.content.parts:

                    texts = []

                    for part in event.content.parts:
                        if part.text:
                            texts.append(part.text)

                    final_response = "\n".join(texts).strip()

    except Exception as e:

        print("Agent error:", repr(e))

        return (
            "❌ Sorry, I could not process your request.\n\n"
            f"Error: {str(e)}"
        )

    if not final_response:
        return "⚠️ I could not generate a response."

    return final_response


# =========================================================
# FIND GENERATED FILE
# =========================================================

# =========================================================
# FIND GENERATED FILE
# =========================================================
def find_generated_file(response: str):
    """
    Find a PDF or PPTX only when the current agent response
    explicitly contains its generated file path.

    Important:
    We do NOT fall back to the latest existing file because
    that could send an old PDF/PPTX for an unrelated request.
    """
    import re

    if not response:
        return None

    # =====================================================
    # PDF FROM CURRENT RESPONSE
    # =====================================================
    pdf_match = re.search(
        r"data[\\/]+invoices[\\/]+([^`\s]+\.pdf)",
        response,
        re.IGNORECASE,
    )

    if pdf_match:
        filename = pdf_match.group(1).strip("`.,);")

        pdf_path = INVOICE_DIR / filename

        if pdf_path.exists():
            return pdf_path

    # =====================================================
    # PPTX FROM CURRENT RESPONSE
    # =====================================================
    pptx_match = re.search(
        r"data[\\/]+analysis[\\/]+([^`\s]+\.pptx)",
        response,
        re.IGNORECASE,
    )

    if pptx_match:
        filename = pptx_match.group(1).strip("`.,);")

        pptx_path = REPORT_DIR / filename

        if pptx_path.exists():
            return pptx_path

    # =====================================================
    # NO FILE GENERATED FOR THIS REQUEST
    # =====================================================
    return None


# =========================================================
# START COMMAND
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    welcome_message = (
        "🛒 Welcome to Supermarket Ops Agent!\n\n"
        "I can help you manage your supermarket through Telegram.\n\n"
        "You can ask me things like:\n\n"
        "📦 Check stock of Maggi\n"
        "📥 Receive 10 packets of Tata Salt\n"
        "⚠️ Show low stock products\n"
        "🧾 Create a bill\n"
        "💰 Complete a cash/UPI/card bill\n"
        "📒 Create a credit bill\n"
        "👤 Check customer balance\n"
        "💵 Record customer payment\n"
        "📄 Generate an invoice\n"
        "📊 Generate today's sales report\n\n"
        "Just send me your request."
    )

    await update.message.reply_text(
        welcome_message
    )


# =========================================================
# HANDLE NORMAL MESSAGES
# =========================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return

    if not update.message.text:
        return

    user_message = update.message.text.strip()

    if not user_message:
        return

    # -----------------------------------------------------
    # Telegram user ID
    # -----------------------------------------------------

    user_id = str(
        update.effective_user.id
    )

    print(
        f"\nTelegram User {user_id}: "
        f"{user_message}"
    )

    # -----------------------------------------------------
    # Send temporary processing message
    # -----------------------------------------------------

    processing_message = await update.message.reply_text(
        "⏳ Processing your request..."
    )

    # -----------------------------------------------------
    # Ask Gemini ADK agent
    # -----------------------------------------------------

    response = await ask_agent(
        user_id,
        user_message,
    )

    print(
        f"Agent Response:\n{response}\n"
    )

    # -----------------------------------------------------
    # Delete processing message
    # -----------------------------------------------------

    try:

        await processing_message.delete()

    except Exception:

        pass

    # -----------------------------------------------------
    # Send agent response
    # -----------------------------------------------------

    await update.message.reply_text(
        response
    )

    # -----------------------------------------------------
    # Check whether a PDF/PPTX was generated
    # -----------------------------------------------------

    generated_file = find_generated_file(
        response
    )

    if not generated_file:

        return

    print(
        f"Generated file found: "
        f"{generated_file}"
    )

    # -----------------------------------------------------
    # Verify file exists
    # -----------------------------------------------------

    if not generated_file.exists():

        print(
            f"File does not exist: "
            f"{generated_file}"
        )

        return

    # -----------------------------------------------------
    # Determine file type
    # -----------------------------------------------------

    suffix = generated_file.suffix.lower()

    if suffix == ".pdf":

        caption = (
            "🧾 Invoice generated successfully."
        )

    elif suffix == ".pptx":

        caption = (
            "📊 Daily sales report "
            "generated successfully."
        )

    else:

        caption = (
            "📎 Generated file"
        )

    # -----------------------------------------------------
    # SEND FILE TO TELEGRAM
    # -----------------------------------------------------

    try:

        with open(
            generated_file,
            "rb"
        ) as file:

            await update.message.reply_document(
                document=file,
                filename=generated_file.name,
                caption=caption,
            )

        print(
            f"File sent successfully: "
            f"{generated_file.name}"
        )

    except Exception as e:

        print(
            "Telegram file sending error:",
            repr(e)
        )

        await update.message.reply_text(
            "⚠️ The file was generated, "
            "but Telegram could not send "
            "the attachment.\n\n"
            f"File: {generated_file.name}"
        )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    print(
        "Telegram bot error:",
        repr(context.error)
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "========================================"
    )

    print(
        "🛒 Supermarket Ops Agent"
    )

    print(
        "Telegram bot starting..."
    )

    print(
        "========================================"
    )

    # -----------------------------------------------------
    # Create Telegram application
    # -----------------------------------------------------

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    # -----------------------------------------------------
    # Commands
    # -----------------------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    # -----------------------------------------------------
    # Text messages
    # -----------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            handle_message,
        )
    )

    # -----------------------------------------------------
    # Error handler
    # -----------------------------------------------------

    application.add_error_handler(
        error_handler
    )

    # -----------------------------------------------------
    # Start bot
    # -----------------------------------------------------

    print(
        "✅ Telegram bot is running..."
    )

    print(
        "Press Ctrl+C to stop."
    )

    application.run_polling()


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()