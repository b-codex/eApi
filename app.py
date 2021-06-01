from routes.routes import *

app.register_blueprint(bp, url_prefix="")

if __name__ == '__main__':
    app.run(debug=True)