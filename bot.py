
import io
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Keys (ඔබේ Telegram Token සහ Gemini API Key මෙතැනට දාන්න)
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

# Gemini Client
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# 1. Start Command (Welcome Message - Sinhala & English)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome! / ආයුබෝවන්!**\n\n"
        "🇱🇰 **සිංහල:**\n"
        "මම දැන් සම්පූර්ණ AI සහකාරකයක් ලෙස ක්‍රියා කරමි!\n"
        "• **කතා කිරීමට සහ ඉගෙන ගැනීමට:** ඕනෑම අධ්‍යාපනික ප්‍රශ්නයක්, විද්‍යාත්මක ගැටළුවක් හෝ සාමාන්‍ය දෙයක් අසන්න.\n"
        "• **කේත ලිවීමට (Coding):** Python, JavaScript හෝ ඕනෑම භාෂාවකින් කේත ලිවීමට, වැරදි (Errors) හදා ගැනීමට මගෙන් ඉල්ලා සිටින්න.\n"
        "• **ඡායාරූප සදා ගැනීමට:** `/image` සමඟ ඔබට අවශ්‍ය විස්තරය (Prompt) ලබා දෙන්න.\n\n"
        "--- \n\n"
        "🇬🇧 **English:**\n"
        "I am now fully upgraded to act like a smart AI assistant!\n"
        "• **To Chat & Study:** Ask any educational question, coding help, or general inquiry.\n"
        "• **To Code:** Ask me to write, debug, or explain programs in Python, JS, etc.\n"
        "• **To Generate Images:** Use `/image` followed by your prompt."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# 2. Advanced Chat & Coding Handler (Sinhala & English)
async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    # Send typing status
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # බොට් හට ඔබ මෙන් (Smart AI Assistant) වැඩ කිරීමට පද්ධති උපදෙස් ලබා දීම
        system_instruction = (
            "You are an advanced, helpful AI assistant, very similar to Google Gemini. "
            "You can write code, explain complex topics, solve math problems, and help with studies. "
            "The user can speak in Sinhala or English. Always reply in the exact same language "
            "that the user used, with clear formatting and code blocks if needed."
        )
        
        # gemini-2.5-flash හෝ වඩාත්ම සුදුසු මාදිලිය භාවිතා කිරීම
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{system_instruction}\n\nUser Request: {user_message}",
        )
        
        # දිගු පිළිතුරු Telegram හරහා යැවීමේදී ගැටළු මඟහරවා ගැනීමට කොටස් වශයෙන් හෝ කෙලින්ම යැවීම
        reply_text = response.text
        if len(reply_text) > 4000:
            for i in range(0, len(reply_text), 4000):
                await update.message.reply_text(reply_text[i:i+4000])
        else:
            await update.message.reply_text(reply_text)
            
    except Exception as e:
        error_msg = (
            "⚠️ කණගාටුයි, දෝෂයක් සිදු විය / Sorry, an error occurred:\n"
            f"{str(e)}"
        )
        await update.message.reply_text(error_msg)

# 3. Image Generation Handler (Sinhala & English)
async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    
    if not prompt:
        prompt_warning = (
            "⚠️ **කරුණාකර රූපයේ විස්තරයක් ලබාදෙන්න / Please provide an image description:**\n"
            "• **සිංහල:** `/image a futuristic city` ලෙස යවන්න.\n"
            "• **English:** Send like `/image a futuristic city`."
        )
        await update.message.reply_text(prompt_warning, parse_mode="Markdown")
        return

    status_text = (
        "🎨 **ඔබගේ ඡායාරූපය සාදමින් පවතී...**\n"
        "🎨 **Generating your image...**"
    )
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
    await update.message.reply_text(status_text, parse_mode="Markdown")

    try:
        # Generate Image using Imagen 3 model
        result = ai_client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1"
            )
        )

        for generated_image in result.generated_images:
            image_bytes = generated_image.image.image_bytes
            bio = io.BytesIO(image_bytes)
            bio.name = 'generated_image.png'
            bio.seek(0)
            
            caption_text = f"🖼 **Prompt / විස්තරය:** {prompt}"
            await update.message.reply_photo(photo=bio, caption=caption_text, parse_mode="Markdown")
            
    except Exception as e:
        error_img_msg = (
            "❌ ඡායාරූපය සෑදීමේදී දෝෂයක් විය / Error generating image:\n"
            f"{str(e)}"
        )
        await update.message.reply_text(error_img_msg)

# Main Function
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("image", image_handler))
    app.add_handler(CommandHandler("photo", image_handler))

    # Text Messages
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_handler))

    print("Advanced AI Bot is running successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()