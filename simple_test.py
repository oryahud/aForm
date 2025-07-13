#!/usr/bin/env python3
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Flask Test Server</h1><p>If you can see this, the server is working!</p>'

if __name__ == '__main__':
    print("Starting simple test server on http://127.0.0.1:4000")
    app.run(host='127.0.0.1', port=4000, debug=True, use_reloader=False)