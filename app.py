from flask import Flask, request, render_template, g, Response
import sqlite3
import csv
import telebot

app = Flask(__name__)

DATABASE = 'messages.db'
BOT_TOKEN = "5900191326:AAH9RSN4n_K9xvhOF4D8YKoqjhAIkXby1eI"

bot = telebot.TeleBot(BOT_TOKEN)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Define the index route
@app.route("/")
def index():
    # Get the custom messages from the database
    c = get_db().cursor()
    c.execute("SELECT language, message_key, message FROM messages ORDER BY language, message_key")
    rows = c.fetchall()
    custom_messages = {}
    for row in rows:
        language, message_key, message = row
        if language not in custom_messages:
            custom_messages[language] = {}
        if message_key not in custom_messages[language]:
            custom_messages[language][message_key] = []
        custom_messages[language][message_key].append(message)

    return render_template("index.html", custom_messages=custom_messages)

# Define the update_messages route
@app.route("/update_messages", methods=["POST"])
def update_messages():
    # Get the form data
    language = request.form.get("language")
    message_key = request.form.get("message_key")
    new_messages = request.form.getlist("new_messages")

    # Delete the old messages from the database
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE language=? AND message_key=?", (language, message_key))

    # Insert the new messages into the database
    for new_message in new_messages:
        # Check if the new message is empty
        if not new_message:
            return "Error: The message cannot be empty."

        c.execute("INSERT INTO messages (language, message_key, message) VALUES (?, ?, ?)", (language, message_key, new_message))

    # Commit the changes to the database
    conn.commit()

    return index()

@app.route("/send_update", methods=["POST"])
def send_update():
  # Get the form data
  language = request.form.get("language")
  update_message = request.form.get("update_message")

  # Check if the update message is empty
  if not update_message:
      return "Error: The update message cannot be empty."

  # Get the chat IDs of users who have selected the specified language
  conn = get_db()
  c = conn.cursor()
  c.execute("SELECT chat_id FROM users WHERE language=?", (language,))
  chat_ids = [row[0] for row in c.fetchall()]

  # Send the update message to each user
  for chat_id in chat_ids:
      bot.send_message(chat_id, update_message)

  return index()

@app.route("/export_users")
def export_users():
  # Get the user data from the database
  c = get_db().cursor()
  c.execute("SELECT chat_id, language, email, contact_number FROM users ORDER BY chat_id")
  rows = c.fetchall()

  # Create a CSV file with the user data
  csv_data = [["Chat ID", "Language", "Email", "Contact Number"]]
  for row in rows:
      csv_data.append(list(row))

  # Create a response with the CSV data
  response = Response(content_type="text/csv")
  response.headers["Content-Disposition"] = "attachment; filename=users.csv"
  writer = csv.writer(response)
  writer.writerows(csv_data)

  return response

@app.route("/footer")
def footer():
  return """
<a href="#" onclick="window.open('https://www.sitelock.com/verify.php?site=lord-of-cyprus.app','SiteLock','width=600,height=600,left=160,top=170');" ><img class="img-fluid" alt="SiteLock" title="SiteLock" src="https://shield.sitelock.com/shield/lord-of-cyprus.app" /></a>
"""

if __name__ == "__main__":
    app.run()
