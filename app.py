from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create-form', methods=['POST'])
def create_form():
    return jsonify({'message': 'Form creation started!', 'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)