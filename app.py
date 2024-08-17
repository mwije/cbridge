from cbridge import create_app

flask_app = create_app()

APP_PORT = 8880

if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', debug=True, port=APP_PORT)