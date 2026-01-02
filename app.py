from flask import Flask
from dotenv import load_dotenv
import os

# Import blueprints
from routes.main import main_bp
from routes.goals import goals_bp
from routes.habits import habits_bp
from routes.reminders import reminders_bp
from routes.gita import gita_bp
from routes.books import books_bp
from routes.notes import notes_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(goals_bp)
app.register_blueprint(habits_bp)
app.register_blueprint(reminders_bp)
app.register_blueprint(gita_bp)
app.register_blueprint(books_bp)
app.register_blueprint(notes_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
