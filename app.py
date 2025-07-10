from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)

def load_forms():
    if os.path.exists('forms.json'):
        with open('forms.json', 'r') as f:
            return json.load(f)
    return []

def save_forms(forms):
    with open('forms.json', 'w') as f:
        json.dump(forms, f, indent=2)

@app.route('/')
def index():
    forms = load_forms()
    return render_template('index.html', has_forms=len(forms) > 0)

@app.route('/create-form', methods=['POST'])
def create_form():
    data = request.get_json()
    form_name = data.get('name', '').strip()
    
    if not form_name:
        return jsonify({'error': 'Form name is required'}), 400
    
    forms = load_forms()
    
    # Check if form name already exists
    if any(form['name'] == form_name for form in forms):
        return jsonify({'error': 'Form name already exists'}), 400
    
    # Create new form with initial question
    new_form = {
        'name': form_name,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'questions': [
            {
                'id': 'q_1',
                'title': 'Question 1',
                'text': '',
                'type': 'text',
                'required': False
            }
        ]
    }
    
    forms.append(new_form)
    save_forms(forms)
    
    return jsonify({'message': 'Form created successfully!', 'redirect': f'/form/{form_name}'})

@app.route('/form/<form_name>')
def edit_form(form_name):
    forms = load_forms()
    form = next((f for f in forms if f['name'] == form_name), None)
    
    if not form:
        return redirect(url_for('index'))
    
    return render_template('form_builder.html', form=form)

@app.route('/api/form/<form_name>/save', methods=['POST'])
def save_form_data(form_name):
    forms = load_forms()
    form_index = next((i for i, f in enumerate(forms) if f['name'] == form_name), None)
    
    if form_index is None:
        return jsonify({'error': 'Form not found'}), 404
    
    data = request.get_json()
    forms[form_index]['questions'] = data.get('questions', [])
    forms[form_index]['updated_at'] = datetime.now().isoformat()
    
    save_forms(forms)
    return jsonify({'message': 'Form saved successfully'})

@app.route('/api/form/<form_name>/question', methods=['POST'])
def add_question(form_name):
    forms = load_forms()
    form_index = next((i for i, f in enumerate(forms) if f['name'] == form_name), None)
    
    if form_index is None:
        return jsonify({'error': 'Form not found'}), 404
    
    questions = forms[form_index]['questions']
    question_num = len(questions) + 1
    new_question = {
        'id': f'q_{question_num}',
        'title': f'Question {question_num}',
        'text': '',
        'type': 'text',
        'required': False
    }
    
    questions.append(new_question)
    forms[form_index]['updated_at'] = datetime.now().isoformat()
    save_forms(forms)
    
    return jsonify({'question': new_question})

@app.route('/my-forms')
def my_forms():
    forms = load_forms()
    return render_template('my_forms.html', forms=forms)

if __name__ == '__main__':
    app.run(debug=True)