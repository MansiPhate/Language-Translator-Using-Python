from flask import Flask, render_template, request, session, redirect, url_for
from googletrans import Translator
from flask_pymongo import PyMongo
import datetime                    #import datetime to  get the current timestamp
import uuid
from bson import ObjectId

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your_secret_key'

app.config["MONGO_URI"] = "mongodb://localhost:27017/translatorDB"
mongo= PyMongo(app)

translator = Translator()


@app.route('/', methods=['GET', 'POST'])
def index():
    translated_text = ""
    translations = []
    
    # Initialize the session translations if they don't exist
    if 'user_id' not in session:
        # Assign a unique anonymous user ID if the user is anonymous
        session['user_id'] = str(uuid.uuid4())
    
    #Handle translation
    if request.method == 'POST':
        # Get text and target language from the form
        text = request.form['text']
        target_language = request.form['language']
        
        # Translate text
        translation = translator.translate(text, dest=target_language)
        translated_text = translation.text
        
         # Store the original and translated text in MongoDB
        if 'save' in request.form:
            mongo.db.translation.insert_one({
                "user_id": session['user_id'],  # Store the user ID (either logged-in user or anonymous)
                "original_text": text,
                "translated_text": translated_text,
                "language": target_language,
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")      #Store the current timestamp
            })
    
    # Retrieve all translations from the database
    translations = list(mongo.db.translation.find({"user_id": session['user_id']}).sort([('date', -1)]).limit(4))

    # .find() will fetch all documents.
    # .limit(3) ensures that only the top 3 most recent translations are returned.
    
    # If no translations for the user, show a placeholder message
    if not translations:
        no_translations_message = "No translations yet."
    else:
        no_translations_message = None
        
    # Handle deletion of a translation
    if request.args.get('delete_id'):
        delete_id = request.args.get('delete_id')
        mongo.db.translation.delete_one({"_id": ObjectId(delete_id)})
        return redirect(url_for('index'))
    
        @app.route('/export', methods=['GET'])
        def export_history():
            """Export translation history as a JSON file."""
            history = session.get('history', [])
            return jsonify(history)
    
    return render_template('index.html', translated_text=translated_text, translations=translations, no_translations_message=no_translations_message)


if __name__ == '__main__':
    app.run(debug=True)


# Explanation:
# Session Management: We use session['user_id'] to identify whether the user is logged in or anonymous. If it's not present, a unique user_id (UUID) is generated for anonymous users.
# MongoDB: Translations are saved in the MongoDB database under the translations collection with the user's unique user_id, original text, translated text, target language, and timestamp.
# Retrieve Translations: Translations are retrieved from the database for the current user_id (whether anonymous or logged in), and only the latest 5 translations are shown.