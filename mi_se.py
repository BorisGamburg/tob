from flask import Flask
import logging
from waitress import serve

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    logging.info("Маршрут / вызван")
    return "<h1>Тест работает</h1>"

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)