from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import uuid
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
    return render_template('my_forms.html', forms=forms)

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
        'status': 'draft',
        'submissions': [],
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

@app.route('/api/form/<form_name>/publish', methods=['POST'])
def publish_form(form_name):
    forms = load_forms()
    form_index = next((i for i, f in enumerate(forms) if f['name'] == form_name), None)
    
    if form_index is None:
        return jsonify({'error': 'Form not found'}), 404
    
    forms[form_index]['status'] = 'published'
    forms[form_index]['updated_at'] = datetime.now().isoformat()
    save_forms(forms)
    
    share_url = f"{request.url_root}submit/{form_name}"
    return jsonify({'message': 'Form published successfully!', 'share_url': share_url})

@app.route('/api/form/<form_name>/hide', methods=['POST'])
def hide_form(form_name):
    forms = load_forms()
    form_index = next((i for i, f in enumerate(forms) if f['name'] == form_name), None)
    
    if form_index is None:
        return jsonify({'error': 'Form not found'}), 404
    
    forms[form_index]['status'] = 'draft'
    forms[form_index]['updated_at'] = datetime.now().isoformat()
    save_forms(forms)
    
    return jsonify({'message': 'Form hidden successfully!'})

@app.route('/submit/<form_name>')
def public_form(form_name):
    forms = load_forms()
    form = next((f for f in forms if f['name'] == form_name), None)
    
    if not form or form.get('status') != 'published':
        return render_template('error.html', message='Form not found or not published'), 404
    
    return render_template('public_form.html', form=form)

@app.route('/api/form/<form_name>/submit', methods=['POST'])
def submit_form(form_name):
    forms = load_forms()
    form_index = next((i for i, f in enumerate(forms) if f['name'] == form_name), None)
    
    if form_index is None or forms[form_index].get('status') != 'published':
        return jsonify({'error': 'Form not found or not published'}), 404
    
    data = request.get_json()
    responses = data.get('responses', {})
    
    # Create submission
    submission = {
        'id': str(uuid.uuid4()),
        'submitted_at': datetime.now().isoformat(),
        'status': 'pending',
        'responses': responses
    }
    
    # Add to form submissions
    if 'submissions' not in forms[form_index]:
        forms[form_index]['submissions'] = []
    
    forms[form_index]['submissions'].append(submission)
    save_forms(forms)
    
    return jsonify({'message': 'Form submitted successfully!', 'submission_id': submission['id'], 'review_url': f"/review/{submission['id']}/{form_name}"})

@app.route('/form/<form_name>/submissions')
def view_submissions(form_name):
    forms = load_forms()
    form = next((f for f in forms if f['name'] == form_name), None)
    
    if not form:
        return redirect(url_for('index'))
    
    return render_template('submissions.html', form=form)

@app.route('/api/form/<form_name>/submission/<submission_id>/approve', methods=['POST'])
def approve_submission(form_name, submission_id):
    forms = load_forms()
    form_index = next((i for i, f in enumerate(forms) if f['name'] == form_name), None)
    
    if form_index is None:
        return jsonify({'error': 'Form not found'}), 404
    
    submissions = forms[form_index].get('submissions', [])
    submission_index = next((i for i, s in enumerate(submissions) if s['id'] == submission_id), None)
    
    if submission_index is None:
        return jsonify({'error': 'Submission not found'}), 404
    
    data = request.get_json()
    action = data.get('action')  # 'approve' or 'reject'
    
    if action not in ['approve', 'reject']:
        return jsonify({'error': 'Invalid action'}), 400
    
    forms[form_index]['submissions'][submission_index]['status'] = 'approved' if action == 'approve' else 'rejected'
    forms[form_index]['updated_at'] = datetime.now().isoformat()
    save_forms(forms)
    
    return jsonify({'message': f'Submission {action}d successfully'})

@app.route('/api/form/<form_name>/delete', methods=['DELETE'])
def delete_form(form_name):
    forms = load_forms()
    form_index = next((i for i, f in enumerate(forms) if f['name'] == form_name), None)
    
    if form_index is None:
        return jsonify({'error': 'Form not found'}), 404
    
    forms.pop(form_index)
    save_forms(forms)
    
    return jsonify({'message': 'Form deleted successfully'})

@app.route('/review/<submission_id>/<form_name>')
def review_submission(submission_id, form_name):
    forms = load_forms()
    form = next((f for f in forms if f['name'] == form_name), None)
    
    if not form:
        return render_template('error.html', message='Form not found'), 404
    
    submission = next((s for s in form.get('submissions', []) if s['id'] == submission_id), None)
    
    if not submission:
        return render_template('error.html', message='Submission not found'), 404
    
    return render_template('review_submission.html', form=form, submission=submission)

@app.route('/my-forms')
def my_forms():
    forms = load_forms()
    return render_template('my_forms.html', forms=forms)

if __name__ == '__main__':
    app.run(debug=True)