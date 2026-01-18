import sys
import os
import traceback

try:
    sys.path.insert(0, os.path.dirname(__file__))

    from a2wsgi import ASGIMiddleware

    from app.main import app

    application = ASGIMiddleware(app)

except Exception as e:
    with open("passenger_startup_error.log", "w") as f:
        f.write(f"Error during startup:\n{str(e)}\n")
        f.write(traceback.format_exc())
    raise e
