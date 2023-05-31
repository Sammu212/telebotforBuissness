import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect("messages.db")
c = conn.cursor()

# Insert the default messages into the messages table
c.execute("INSERT INTO messages (language, message_key, message) VALUES ('English', 'greeting', 'Hello! Please enter your email:');")
c.execute("INSERT INTO messages (language, message_key, message) VALUES ('English', 'consent', 'Do you consent to receive channel updates?');")
c.execute("INSERT INTO messages (language, message_key, message) VALUES ('English', 'thank_you', 'Thank you! Your email has been added to our system. Please enter your contact number:');")
c.execute("INSERT INTO messages (language, message_key, message) VALUES ('English', 'final_message', 'Thank you {name}! Your information has been saved.');")
c.execute("INSERT INTO messages (language, message_key, message) VALUES ('Deutsch', 'greeting', 'Hallo! Bitte geben Sie Ihre E-Mail-Adresse ein:');")
c.execute("INSERT INTO messages (language, message_key, message) VALUES ('Deutsch', 'consent', 'Stimmen Sie zu, Kanalaktualisierungen zu erhalten?');")
c.execute("INSERT INTO messages (language, message_key, message) VALUES ('Deutsch', 'thank_you', 'Danke! Ihre E-Mail-Adresse wurde zu unserem System hinzugefügt. Bitte geben Sie Ihre Telefonnummer ein:');")
c.execute("INSERT INTO messages (language, message_key, message) VALUES ('Deutsch', 'final_message', 'Danke {name}! Ihre Informationen wurden gespeichert.');")

# Commit the changes to the database
conn.commit()

# Close the database connection
conn.close()
