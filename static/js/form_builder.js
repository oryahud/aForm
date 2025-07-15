// Global state
let currentQuestionIndex = 0;
let hasUnsavedChanges = false;
let lastSavedState = null;

// Helper function to get question type display text
function getQuestionTypeText(type) {
    const typeMap = {
        'text': '📝 Text Input',
        'email': '📧 Email Address',
        'phone': '📱 Phone Number',
        'date': '📅 Date',
        'time': '🕐 Time',
        'url': '🔗 Website URL',
        'number': '🔢 Number',
        'rating': '⭐ Rating Scale',
        'radio': '🔘 Multiple Choice',
        'checkbox': '☑️ Checkboxes',
        'select': '📋 Dropdown',
        'textarea': '📄 Long Text',
        'file': '📎 File Upload'
    };
    return typeMap[type] || '📝 Text Input';
}

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
    
    // Save initial state for unsaved changes detection
    lastSavedState = JSON.stringify(window.formData.questions);
    
    // Add beforeunload event listener
    window.addEventListener('beforeunload', function(e) {
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
});

// Check for unsaved changes
function checkForUnsavedChanges() {
    const currentState = JSON.stringify(window.formData.questions);
    hasUnsavedChanges = currentState !== lastSavedState;
}

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
        
        const typeText = getQuestionTypeText(question.type);
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
    checkForUnsavedChanges();
});

// Placeholder text editing
document.getElementById('placeholderText').addEventListener('input', function(e) {
    window.formData.questions[currentQuestionIndex].placeholder = e.target.value;
    checkForUnsavedChanges();
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
    checkForUnsavedChanges();
});

// Required checkbox change
document.getElementById('questionRequired').addEventListener('change', function(e) {
    window.formData.questions[currentQuestionIndex].required = e.target.checked;
    checkForUnsavedChanges();
});

// Multiple selection change
document.getElementById('allowMultiple').addEventListener('change', function(e) {
    window.formData.questions[currentQuestionIndex].multiple = e.target.checked;
    renderRadioPreview();
    checkForUnsavedChanges();
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
    checkForUnsavedChanges();
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
        checkForUnsavedChanges();
    }
}

// Answer type options management

function toggleAnswerOptions() {
    const answerType = document.getElementById('answerType').value;
    
    // Hide all option groups first
    const allGroups = [
        'optionsGroup', 'textInputGroup', 'phoneGroup', 'dateGroup', 
        'numberGroup', 'ratingGroup', 'fileGroup', 'textareaGroup'
    ];
    
    allGroups.forEach(groupId => {
        const group = document.getElementById(groupId);
        if (group) group.style.display = 'none';
    });
    
    // Show relevant group based on answer type
    switch(answerType) {
        case 'text':
            document.getElementById('textInputGroup').style.display = 'block';
            break;
            
        case 'email':
            // Email uses text input group for placeholder
            document.getElementById('textInputGroup').style.display = 'block';
            break;
            
        case 'phone':
            document.getElementById('phoneGroup').style.display = 'block';
            break;
            
        case 'date':
            document.getElementById('dateGroup').style.display = 'block';
            break;
            
        case 'time':
            // Time doesn't need additional options for now
            break;
            
        case 'url':
            // URL uses text input group for placeholder
            document.getElementById('textInputGroup').style.display = 'block';
            break;
            
        case 'number':
            document.getElementById('numberGroup').style.display = 'block';
            break;
            
        case 'rating':
            document.getElementById('ratingGroup').style.display = 'block';
            break;
            
        case 'radio':
        case 'checkbox':
        case 'select':
            document.getElementById('optionsGroup').style.display = 'block';
            // Initialize with default options if empty
            const question = window.formData.questions[currentQuestionIndex];
            if (!question.options || question.options.length === 0) {
                question.options = ['Option 1', 'Option 2'];
                renderOptions(question.options);
            }
            renderRadioPreview();
            break;
            
        case 'textarea':
            document.getElementById('textareaGroup').style.display = 'block';
            break;
            
        case 'file':
            document.getElementById('fileGroup').style.display = 'block';
            break;
    }
    
    // Update the question type
    if (window.formData.questions[currentQuestionIndex]) {
        window.formData.questions[currentQuestionIndex].type = answerType;
        checkForUnsavedChanges();
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
    checkForUnsavedChanges();
}

function removeOption(index) {
    const question = window.formData.questions[currentQuestionIndex];
    if (question.options.length > 1) {
        question.options.splice(index, 1);
        renderOptions(question.options);
        renderRadioPreview();
        checkForUnsavedChanges();
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
    checkForUnsavedChanges();
}

function renderRadioPreview() {
    const question = window.formData.questions[currentQuestionIndex];
    const preview = document.getElementById('radioOptionsPreview');
    
    if (!['radio', 'checkbox', 'select'].includes(question.type) || !question.options) {
        preview.innerHTML = '';
        return;
    }
    
    let previewHtml = '<h5>Preview:</h5>';
    
    if (question.type === 'select') {
        previewHtml += `
            <select class="form-input" ${question.multiple ? 'multiple' : ''}>
                ${question.options.map(option => `<option value="${option}">${option}</option>`).join('')}
            </select>
        `;
    } else {
        const inputType = (question.type === 'checkbox' || question.multiple) ? 'checkbox' : 'radio';
        const inputName = (inputType === 'radio') ? 'preview-radio' : '';
        
        previewHtml += question.options.map((option, index) => `
            <div class="radio-preview-item">
                <input type="${inputType}" ${inputName ? `name="${inputName}"` : ''} id="preview-${index}">
                <label for="preview-${index}" class="radio-preview-label">${option}</label>
            </div>
        `).join('');
    }
    
    preview.innerHTML = previewHtml;
}

// Add validation functions for new input types
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePhone(phone, countryCode) {
    // Basic phone validation - can be enhanced
    const phoneRegex = /^[\d\s\-\(\)\+\.]+$/;
    return phoneRegex.test(phone) && phone.replace(/\D/g, '').length >= 7;
}

function validateURL(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

function formatRatingDisplay(value, scale, style) {
    switch(style) {
        case 'stars':
            return '★'.repeat(Math.floor(value * 5 / scale)) + '☆'.repeat(5 - Math.floor(value * 5 / scale));
        case 'slider':
            return `${value} / ${scale}`;
        default:
            return value.toString();
    }
}

// Enhanced preview generation for all question types
function generateQuestionPreview(question, index) {
    const required = question.required ? '<span style="color: red;">*</span>' : '';
    let inputHtml = '';
    
    switch(question.type) {
        case 'text':
            inputHtml = `<input type="text" placeholder="${question.placeholder || 'Enter your answer...'}" class="form-input">`;
            break;
            
        case 'email':
            inputHtml = `<input type="email" placeholder="${question.placeholder || 'Enter your email address...'}" class="form-input">`;
            break;
            
        case 'phone':
            const countryCode = question.countryCode || '+1';
            inputHtml = `
                <div style="display: flex; gap: 8px;">
                    <input type="text" value="${countryCode}" disabled style="width: 80px;" class="form-input">
                    <input type="tel" placeholder="Phone number" class="form-input" style="flex: 1;">
                    ${question.allowExtension ? '<input type="text" placeholder="Ext." style="width: 80px;" class="form-input">' : ''}
                </div>
            `;
            break;
            
        case 'date':
            inputHtml = `<input type="date" class="form-input" ${question.minDate ? `min="${question.minDate}"` : ''} ${question.maxDate ? `max="${question.maxDate}"` : ''}>`;
            break;
            
        case 'time':
            inputHtml = `<input type="time" class="form-input">`;
            break;
            
        case 'url':
            inputHtml = `<input type="url" placeholder="${question.placeholder || 'https://example.com'}" class="form-input">`;
            break;
            
        case 'number':
            inputHtml = `<input type="number" class="form-input" 
                ${question.minValue ? `min="${question.minValue}"` : ''} 
                ${question.maxValue ? `max="${question.maxValue}"` : ''}
                ${question.stepSize ? `step="${question.stepSize}"` : ''}
                placeholder="Enter a number">`;
            break;
            
        case 'rating':
            const scale = question.ratingScale || 10;
            const style = question.ratingStyle || 'numbers';
            if (style === 'stars') {
                inputHtml = `<div class="rating-stars">
                    ${Array.from({length: scale}, (_, i) => `<span class="star" data-value="${i+1}">☆</span>`).join('')}
                </div>`;
            } else if (style === 'slider') {
                inputHtml = `<input type="range" min="1" max="${scale}" value="${Math.floor(scale/2)}" class="form-input">
                    <div style="display: flex; justify-content: space-between; font-size: 0.8em; margin-top: 4px;">
                        <span>${question.lowLabel || 'Poor'}</span>
                        <span>${question.highLabel || 'Excellent'}</span>
                    </div>`;
            } else {
                inputHtml = `<select class="form-input">
                    ${Array.from({length: scale}, (_, i) => `<option value="${i+1}">${i+1}</option>`).join('')}
                </select>`;
            }
            break;
            
        case 'textarea':
            const rows = question.textareaRows || 4;
            const charLimit = question.charLimit ? `maxlength="${question.charLimit}"` : '';
            inputHtml = `<textarea rows="${rows}" ${charLimit} placeholder="${question.textareaPlaceholder || 'Enter your detailed response...'}" class="form-input"></textarea>`;
            break;
            
        case 'file':
            const accept = question.fileTypes ? question.fileTypes.join(',') : '';
            const multiple = question.allowMultipleFiles ? 'multiple' : '';
            inputHtml = `<input type="file" ${accept ? `accept="${accept}"` : ''} ${multiple} class="form-input">
                <small style="color: #666;">Max size: ${question.maxFileSize || 10}MB</small>`;
            break;
            
        case 'radio':
        case 'checkbox':
        case 'select':
            if (question.type === 'select') {
                inputHtml = `<select class="form-input" ${question.multiple ? 'multiple' : ''}>
                    ${(question.options || []).map(option => `<option value="${option}">${option}</option>`).join('')}
                </select>`;
            } else {
                const inputType = (question.type === 'checkbox' || question.multiple) ? 'checkbox' : 'radio';
                const inputName = inputType === 'radio' ? `question_${index}` : '';
                inputHtml = (question.options || []).map((option, optIndex) => `
                    <div class="option-item">
                        <input type="${inputType}" ${inputName ? `name="${inputName}"` : ''} id="q${index}_${optIndex}" value="${option}">
                        <label for="q${index}_${optIndex}">${option}</label>
                    </div>
                `).join('');
            }
            break;
            
        default:
            inputHtml = `<input type="text" placeholder="Enter your answer..." class="form-input">`;
    }
    
    return `
        <div class="question-preview">
            <label class="question-label">${question.title}${required}</label>
            <div class="question-input">${inputHtml}</div>
        </div>
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
            // Update saved state and reset unsaved changes flag
            lastSavedState = JSON.stringify(window.formData.questions);
            hasUnsavedChanges = false;
            
            // Show success message - find the save button in modern template
            const saveBtn = document.querySelector('button[onclick="saveForm()"]') || 
                           document.querySelector('.header-actions .create-form-btn');
            
            if (saveBtn) {
                const originalText = saveBtn.innerHTML;
                saveBtn.innerHTML = '<i data-feather="check"></i> Saved!';
                saveBtn.style.background = '#10b981';
                saveBtn.style.borderColor = '#10b981';
                
                // Replace feather icons
                if (typeof feather !== 'undefined') {
                    feather.replace();
                }
                
                setTimeout(() => {
                    saveBtn.innerHTML = originalText;
                    saveBtn.style.background = '';
                    saveBtn.style.borderColor = '';
                    
                    // Replace feather icons again
                    if (typeof feather !== 'undefined') {
                        feather.replace();
                    }
                }, 2000);
            }
            
            return true;
        } else {
            alert('Failed to save form. Please try again.');
            return false;
        }
    } catch (error) {
        console.error('Error saving form:', error);
        alert('Failed to save form. Please try again.');
        return false;
    }
}

// Toggle publish/hide form
async function togglePublish() {
    const isPublished = window.formData.status === 'published';
    const action = isPublished ? 'hide' : 'publish';
    
    try {
        const response = await fetch(`/api/form/${window.formData.name}/${action}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Update form status
            window.formData.status = isPublished ? 'draft' : 'published';
            
            // Update button
            const publishBtn = document.getElementById('publishBtn');
            const publishBtnText = document.getElementById('publishBtnText');
            
            if (isPublished) {
                // Form was hidden
                publishBtnText.textContent = 'Publish';
                publishBtn.style.background = '#007aff';
                alert('Form hidden successfully!');
            } else {
                // Form was published
                publishBtnText.textContent = 'Hide';
                publishBtn.style.background = '#ff9500';
                
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
            }
        } else {
            alert(`Failed to ${action} form. Please try again.`);
        }
    } catch (error) {
        console.error(`Error ${action}ing form:`, error);
        alert(`Failed to ${action} form. Please try again.`);
    }
}

// View submissions
async function viewSubmissions() {
    if (hasUnsavedChanges) {
        if (confirm('You have unsaved changes. Do you want to save before leaving?')) {
            const saved = await saveForm();
            if (saved) {
                window.location.href = `/form/${window.formData.name}/submissions`;
            }
        } else {
            window.location.href = `/form/${window.formData.name}/submissions`;
        }
    } else {
        window.location.href = `/form/${window.formData.name}/submissions`;
    }
}

// Go back to forms
async function goBackToForms() {
    if (hasUnsavedChanges) {
        if (confirm('You have unsaved changes. Do you want to save before leaving?')) {
            const saved = await saveForm();
            if (saved) {
                window.location.href = '/my-forms';
            }
        } else {
            window.location.href = '/my-forms';
        }
    } else {
        window.location.href = '/my-forms';
    }
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