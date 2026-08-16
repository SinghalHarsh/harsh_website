from flask import Flask

from app.config import Config

BLUEPRINTS = (
    "main",
    "goals",
    "habits",
    "reminders",
    "gita",
    "books",
    "notes",
    "diary",
    "pranayama",
)


def create_app(config_class=Config):
    config_class.validate()

    app = Flask(__name__)
    app.config.from_object(config_class)
    app.secret_key = config_class.SECRET_KEY

    from importlib import import_module

    for name in BLUEPRINTS:
        module = import_module(f"app.routes.{name}")
        app.register_blueprint(getattr(module, f"{name}_bp"))

    @app.context_processor
    def inject_globals():
        return {"site_name": config_class.SITE_NAME}

    return app
