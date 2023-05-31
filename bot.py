import telebot
import sqlite3
import threading
import re

bot = telebot.TeleBot("5900191326:AAH9RSN4n_K9xvhOF4D8YKoqjhAIkXby1eI")

# Create a thread-local storage object
thread_local = threading.local()

# Define a function to get the SQLite connection for the current thread
def get_conn():
    # Check if the current thread has a connection
    if not hasattr(thread_local, "conn"):
        # Create a new connection for the current thread
        thread_local.conn = sqlite3.connect("messages.db")
    return thread_local.conn

# Connect to the SQLite database
conn = get_conn()
c = conn.cursor()

# Create the messages table if it doesn't exist
c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        language TEXT,
        message_key TEXT,
        message TEXT
    )
""")
conn.commit()

# Create the users table if it doesn't exist
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        language TEXT,
        email TEXT,
        contact_number TEXT
    )
""")
conn.commit()

# Define the default messages for each language
default_messages = {
    "English": {
        "language_selection": "Which language would you like to continue with?",
        "greeting": "Hello! Please enter your email:",
        "invalid_email": "The email you entered is invalid. Please enter a valid email:",
        "duplicate_email": "The email you entered is already in our system. Please enter a different email:",
        "consent": "Do you consent to receive channel updates?",
        "thank_you": "Thank you! Your email has been added to our system. Please enter your contact number:",
        "final_message": "Thank you {name}! Your information has been saved."
    },
    "Deutsch": {
        "language_selection": "Mit welcher Sprache möchten Sie fortfahren?",
        "greeting": "Hallo! Bitte geben Sie Ihre E-Mail-Adresse ein:",
        "invalid_email": "Die von Ihnen eingegebene E-Mail-Adresse ist ungültig. Bitte geben Sie eine gültige E-Mail-Adresse ein:",
        "duplicate_email": "Die von Ihnen eingegebene E-Mail-Adresse ist bereits in unserem System vorhanden. Bitte geben Sie eine andere E-Mail-Adresse ein:",
        "consent": "Stimmen Sie zu, Kanalaktualisierungen zu erhalten?",
        "thank_you": "Danke! Ihre E-Mail-Adresse wurde zu unserem System hinzugefügt. Bitte geben Sie Ihre Telefonnummer ein:",
        "final_message": "Danke {name}! Ihre Informationen wurden gespeichert."
    }
}

# Define the user data
user_data = {}

# Handle the start command
@bot.message_handler(commands=['start'])
def handle_start(message):
    # Create an inline keyboard with the available languages
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    buttons = [telebot.types.InlineKeyboardButton(text=language, callback_data=f"language_{language}") for language in default_messages.keys()]
    keyboard.add(*buttons)

    # Send the language selection message
    bot.send_message(message.chat.id, default_messages["English"]["language_selection"], reply_markup=keyboard)

# Handle callback queries from inline keyboards
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    # Get the SQLite connection and cursor for the current thread
    conn = get_conn()
    c = conn.cursor()

    # Check if the user has selected a language
    if call.data.startswith("language_"):
        # Get the selected language
        language = call.data.split("_")[1]

        # Save the user's language
        user_data[call.message.chat.id] = {"language": language}

        # Get the custom greeting messages from the database
        c.execute("SELECT message FROM messages WHERE language=? AND message_key=?", (language, "greeting"))
        custom_greeting_messages = [row[0] for row in c.fetchall()]

        # Send the greeting messages
        if custom_greeting_messages:
            for greeting_message in custom_greeting_messages:
                bot.send_message(call.message.chat.id, greeting_message)
        else:
            bot.send_message(call.message.chat.id, default_messages[language]["greeting"])
    elif call.message.chat.id in user_data:
      # Check if the user has entered their email
      if not ("email" in user_data[call.message.chat.id] or call.data.startswith("email_")):
          return

      # Get the user's email and validate it
      email = call.data.split("_")[1] if call.data.startswith("email_") else user_data[call.message.chat.id]["email"]
      if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
          # Send the invalid email message
          bot.send_message(call.message.chat.id, default_messages[user_data[call.message.chat.id]["language"]]["invalid_email"])
          return

      # Check if the email is a duplicate
      c.execute("SELECT COUNT(*) FROM users WHERE email=?", (email,))
      if c.fetchone()[0] > 0:
          # Send the duplicate email message
          bot.send_message(call.message.chat.id, default_messages[user_data[call.message.chat.id]["language"]]["duplicate_email"])
          return

      # Save the user's email
      user_data[call.message.chat.id]["email"] = email

      # Create an inline keyboard with an I accept button
      keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
      button = telebot.types.InlineKeyboardButton(text="I accept", callback_data="consent_accept")
      keyboard.add(button)

      # Get the custom consent messages from the database
      c.execute("SELECT message FROM messages WHERE language=? AND message_key=?", (user_data[call.message.chat.id]["language"], "consent"))
      custom_consent_messages = [row[0] for row in c.fetchall()]

      # Send the consent messages
      if custom_consent_messages:
          for consent_message in custom_consent_messages:
              bot.send_message(call.message.chat.id, consent_message)
      else:
          bot.send_message(call.message.chat.id, default_messages[user_data[call.message.chat.id]["language"]]["consent"], reply_markup=keyboard)
    elif call.data == "consent_accept":
        # Get the custom thank you messages from the database
        c.execute("SELECT message FROM messages WHERE language=? AND message_key=?", (user_data[call.message.chat.id]["language"], "thank_you"))
        custom_thank_you_messages = [row[0] for row in c.fetchall()]

        # Send the thank you messages
        if custom_thank_you_messages:
            for thank_you_message in custom_thank_you_messages:
                bot.send_message(call.message.chat.id, thank_you_message)
        else:
            bot.send_message(call.message.chat.id, default_messages[user_data[call.message.chat.id]["language"]]["thank_you"])
    elif call.data.startswith("contact_number_"):
        # Save the user's contact number
        contact_number = call.data.split("_")[1]
        user_data[call.message.chat.id]["contact_number"] = contact_number

        # Save the user's data in the database
        c.execute("INSERT INTO users (chat_id, language, email, contact_number) VALUES (?, ?, ?, ?)", (call.message.chat.id, user_data[call.message.chat.id]["language"], user_data[call.message.chat.id]["email"], user_data[call.message.chat.id]["contact_number"]))
        conn.commit()

        # Get the custom final messages from the database
        c.execute("SELECT message FROM messages WHERE language=? AND message_key=?", (user_data[call.message.chat.id]["language"], "final_message"))
        custom_final_messages = [row[0] for row in c.fetchall()]

        # Send the final thank you messages
        if custom_final_messages:
            for final_message in custom_final_messages:
                bot.send_message(call.message.chat.id, final_message.format(name=call.from_user.first_name))
        else:
            bot.send_message(call.message.chat.id, default_messages[user_data[call.message.chat.id]["language"]]["final_message"].format(name=call.from_user.first_name))

# Handle messages from users
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    pass

# Start polling for bot updates
bot.polling()
