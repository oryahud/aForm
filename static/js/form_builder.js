// Global state
let currentQuestionIndex = 0;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize questions array if it doesn't exist (for old forms)
    if (!window.formData.questions) {
        window.formData.questions = window.formData.steps ? 
            window.formData.steps.flatMap(step => step.questions || []) : 
            [];
    }
    
    renderQuestions();
    if (window.formData.questions.length > 0) {
        selectQuestion(0);
    }
});

// Question management
function renderQuestions() {
    const questionsList = document.getElementById('questionsList');
    questionsList.innerHTML = '';
    
    if (window.formData.questions.length === 0) {
        questionsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">❓</div>
                <p>No questions yet. Click "Add Question" to get started!</p>
            </div>
        `;
        return;
    }
    
    window.formData.questions.forEach((question, index) => {
        const questionItem = document.createElement('div');
        questionItem.className = `question-item ${index === currentQuestionIndex ? 'active' : ''}`;
        questionItem.onclick = () => selectQuestion(index);
        
        const typeText = question.type === 'text' ? 'Text Input' : 'Radio Button';
        const optionsText = question.options ? ` (${question.options.length} options)` : '';
        const multipleText = question.multiple ? ' - Multiple' : '';
        
        questionItem.innerHTML = `
            <div class="question-title">${question.title || `Question ${index + 1}`}</div>
            <div class="question-info">${typeText}${optionsText}${multipleText}</div>
        `;
        
        questionsList.appendChild(questionItem);
    });
}

function selectQuestion(index) {
    currentQuestionIndex = index;
    renderQuestions();
    renderQuestionEditor();
}

function renderQuestionEditor() {
    const question = window.formData.questions[currentQuestionIndex];
    
    // Update question editor fields
    document.getElementById('questionTitle').value = question.title || '';
    document.getElementById('answerType').value = question.type || 'text';
    document.getElementById('questionRequired').checked = question.required || false;
    document.getElementById('allowMultiple').checked = question.multiple || false;
    
    if (question.placeholder) {
        document.getElementById('placeholderText').value = question.placeholder;
    }
    
    toggleAnswerOptions();
    
    if (question.options) {
        renderOptions(question.options);
        renderRadioPreview();
    }
}

// Question title editing
document.getElementById('questionTitle').addEventListener('input', function(e) {
    window.formData.questions[currentQuestionIndex].title = e.target.value;
    renderQuestions();
});

// Placeholder text editing
document.getElementById('placeholderText').addEventListener('input', function(e) {
    window.formData.questions[currentQuestionIndex].placeholder = e.target.value;
});

// Answer type change
document.getElementById('answerType').addEventListener('change', function(e) {
    const question = window.formData.questions[currentQuestionIndex];
    question.type = e.target.value;
    
    if (e.target.value === 'text') {
        delete question.options;
        delete question.multiple;
        if (!question.placeholder) {
            question.placeholder = '';
        }
    } else if (e.target.value === 'radio') {
        delete question.placeholder;
        if (!question.options) {
            question.options = ['Option 1', 'Option 2'];
        }
        question.multiple = question.multiple || false;
    }
    
    toggleAnswerOptions();
    renderQuestions();
});

// Required checkbox change
document.getElementById('questionRequired').addEventListener('change', function(e) {
    window.formData.questions[currentQuestionIndex].required = e.target.checked;
});

// Multiple selection change
document.getElementById('allowMultiple').addEventListener('change', function(e) {
    window.formData.questions[currentQuestionIndex].multiple = e.target.checked;
    renderRadioPreview();
});

// Question operations
function addQuestion() {
    const questionNum = window.formData.questions.length + 1;
    const newQuestion = {
        id: `q_${questionNum}`,
        title: `Question ${questionNum}`,
        text: '',
        type: 'text',
        required: false
    };
    
    window.formData.questions.push(newQuestion);
    selectQuestion(window.formData.questions.length - 1);
}

function deleteCurrentQuestion() {
    if (window.formData.questions.length <= 1) {
        alert('Cannot delete the last question. A form must have at least one question.');
        return;
    }
    
    if (confirm('Are you sure you want to delete this question?')) {
        window.formData.questions.splice(currentQuestionIndex, 1);
        
        // Adjust current question index
        if (currentQuestionIndex >= window.formData.questions.length) {
            currentQuestionIndex = window.formData.questions.length - 1;
        }
        
        selectQuestion(currentQuestionIndex);
    }
}

// Answer type options management

function toggleAnswerOptions() {
    const answerType = document.getElementById('answerType').value;
    const optionsGroup = document.getElementById('optionsGroup');
    const textInputGroup = document.getElementById('textInputGroup');
    
    if (answerType === 'text') {
        optionsGroup.style.display = 'none';
        textInputGroup.style.display = 'block';
    } else if (answerType === 'radio') {
        textInputGroup.style.display = 'none';
        optionsGroup.style.display = 'block';
        
        // Initialize with default options if empty
        const question = window.formData.questions[currentQuestionIndex];
        if (!question.options || question.options.length === 0) {
            question.options = ['Option 1', 'Option 2'];
            renderOptions(question.options);
        }
        renderRadioPreview();
    }
}

function addOption(text = '') {
    const question = window.formData.questions[currentQuestionIndex];
    if (!question.options) {
        question.options = [];
    }
    
    question.options.push(text || `Option ${question.options.length + 1}`);
    renderOptions(question.options);
    renderRadioPreview();
}

function removeOption(index) {
    const question = window.formData.questions[currentQuestionIndex];
    if (question.options.length > 1) {
        question.options.splice(index, 1);
        renderOptions(question.options);
        renderRadioPreview();
    } else {
        alert('A question must have at least one option.');
    }
}

function renderOptions(options) {
    const optionsList = document.getElementById('optionsList');
    optionsList.innerHTML = '';
    
    options.forEach((option, index) => {
        const optionItem = document.createElement('div');
        optionItem.className = 'option-item';
        
        optionItem.innerHTML = `
            <input type="text" placeholder="Option text..." value="${option}" onchange="updateOption(${index}, this.value)">
            <button class="remove-option-btn" onclick="removeOption(${index})">Remove</button>
        `;
        
        optionsList.appendChild(optionItem);
    });
}

function updateOption(index, value) {
    const question = window.formData.questions[currentQuestionIndex];
    question.options[index] = value;
    renderRadioPreview();
}

function renderRadioPreview() {
    const question = window.formData.questions[currentQuestionIndex];
    const preview = document.getElementById('radioOptionsPreview');
    
    if (question.type !== 'radio' || !question.options) {
        preview.innerHTML = '';
        return;
    }
    
    const inputType = question.multiple ? 'checkbox' : 'radio';
    const inputName = question.multiple ? '' : 'preview-radio';
    
    preview.innerHTML = `
        <h5>Preview:</h5>
        ${question.options.map((option, index) => `
            <div class="radio-preview-item">
                <input type="${inputType}" ${inputName ? `name="${inputName}"` : ''} id="preview-${index}">
                <label for="preview-${index}" class="radio-preview-label">${option}</label>
            </div>
        `).join('')}
    `;
}

// Form saving

async function saveForm() {
    try {
        const response = await fetch(`/api/form/${window.formData.name}/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                questions: window.formData.questions
            })
        });
        
        if (response.ok) {
            // Show success message
            const saveBtn = document.querySelector('.header-actions .create-form-btn');
            const originalText = saveBtn.textContent;
            saveBtn.textContent = 'Saved!';
            saveBtn.style.background = '#34c759';
            
            setTimeout(() => {
                saveBtn.textContent = originalText;
                saveBtn.style.background = '';
            }, 2000);
        } else {
            alert('Failed to save form. Please try again.');
        }
    } catch (error) {
        console.error('Error saving form:', error);
        alert('Failed to save form. Please try again.');
    }
}

// Publish form
async function publishForm() {
    try {
        const response = await fetch(`/api/form/${window.formData.name}/publish`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Show success with share URL
            const publishBtn = document.querySelector('.publish-btn');
            publishBtn.textContent = 'Published!';
            publishBtn.style.background = '#34c759';
            
            // Show share URL
            const shareUrl = data.share_url;
            const message = `Form published successfully!\n\nShare this link:\n${shareUrl}`;
            alert(message);
            
            // Copy to clipboard
            navigator.clipboard.writeText(shareUrl).then(() => {
                console.log('Share URL copied to clipboard');
            }).catch(() => {
                console.log('Could not copy to clipboard');
            });
            
            setTimeout(() => {
                publishBtn.textContent = 'Publish';
                publishBtn.style.background = '';
            }, 3000);
        } else {
            alert('Failed to publish form. Please try again.');
        }
    } catch (error) {
        console.error('Error publishing form:', error);
        alert('Failed to publish form. Please try again.');
    }
}

// View submissions
function viewSubmissions() {
    window.location.href = `/form/${window.formData.name}/submissions`;
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey || e.metaKey) {
        if (e.key === 's') {
            e.preventDefault();
            saveForm();
        }
    }
});