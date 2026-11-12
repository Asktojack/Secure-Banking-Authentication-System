
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from flask import Flask, render_template
from flask_mail import Mail
from config import Config
from routes.auth import auth

app = Flask(__name__)
app.config.from_object(Config)

# Secret key for session
app.secret_key = Config.SECRET_KEY

# Initialize Flask-Mail
mail = Mail(app)

# Register Blueprint
app.register_blueprint(auth)

# Make mail object available in routes
app.mail = mail


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )
