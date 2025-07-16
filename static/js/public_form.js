document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('publicForm');
    
    if (!form) {
        console.error('Form element not found');
        return;
    }
    
    // Initialize interactive elements
    initializeRatingStars();
    initializeCharacterCounters();
    
    // Rating stars functionality
    function initializeRatingStars() {
        const ratingStars = document.querySelectorAll('.rating-stars');
        ratingStars.forEach(ratingGroup => {
            const stars = ratingGroup.querySelectorAll('.star');
            const hiddenInput = ratingGroup.parentElement.querySelector('input[type="hidden"]');
            
            stars.forEach((star, index) => {
                star.addEventListener('click', function() {
                    const value = this.dataset.value;
                    hiddenInput.value = value;
                    
                    // Update star display
                    stars.forEach((s, i) => {
                        if (i < value) {
                            s.textContent = '★';
                            s.classList.add('active');
                        } else {
                            s.textContent = '☆';
                            s.classList.remove('active');
                        }
                    });
                });
                
                star.addEventListener('mouseenter', function() {
                    const value = this.dataset.value;
                    stars.forEach((s, i) => {
                        if (i < value) {
                            s.textContent = '★';
                        } else {
                            s.textContent = '☆';
                        }
                    });
                });
                
                star.addEventListener('mouseleave', function() {
                    const currentValue = hiddenInput.value;
                    stars.forEach((s, i) => {
                        if (i < currentValue) {
                            s.textContent = '★';
                        } else {
                            s.textContent = '☆';
                        }
                    });
                });
            });
        });
    }
    
    // Character counter functionality
    function initializeCharacterCounters() {
        const textareas = document.querySelectorAll('textarea[maxlength]');
        textareas.forEach(textarea => {
            const counter = document.getElementById(textarea.id + '_counter');
            if (counter) {
                textarea.addEventListener('input', function() {
                    counter.textContent = this.value.length;
                });
            }
        });
    }
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('Form submitted, processing...');
        
        const submitBtn = form.querySelector('.submit-btn');
        const originalText = submitBtn.textContent;
        
        // Show loading state
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';
        
        try {
            // Collect form data
            const formData = new FormData(form);
            const responses = {};
            
            // Process each question
            window.formData.questions.forEach(question => {
                switch(question.type) {
                    case 'text':
                    case 'email':
                    case 'url':
                    case 'date':
                    case 'time':
                    case 'number':
                    case 'textarea':
                        responses[question.id] = formData.get(question.id) || '';
                        break;
                        
                    case 'phone':
                        responses[question.id] = formData.get(question.id) || '';
                        // Include extension if present
                        const ext = formData.get(question.id + '_ext');
                        if (ext) {
                            responses[question.id + '_ext'] = ext;
                        }
                        break;
                        
                    case 'rating':
                        responses[question.id] = formData.get(question.id) || '';
                        break;
                        
                    case 'file':
                        // File handling - get file info
                        const fileInput = form.querySelector(`input[name="${question.id}"]`);
                        if (fileInput && fileInput.files.length > 0) {
                            responses[question.id] = Array.from(fileInput.files).map(file => ({
                                name: file.name,
                                size: file.size,
                                type: file.type
                            }));
                        } else {
                            responses[question.id] = [];
                        }
                        break;
                        
                    case 'select':
                        if (question.multiple) {
                            const values = formData.getAll(question.id + '[]');
                            responses[question.id] = values;
                        } else {
                            responses[question.id] = formData.get(question.id) || '';
                        }
                        break;
                        
                    case 'checkbox':
                        const checkboxValues = formData.getAll(question.id + '[]');
                        responses[question.id] = checkboxValues;
                        break;
                        
                    case 'radio':
                        if (question.multiple) {
                            // Multiple selection (checkboxes)
                            const values = formData.getAll(question.id + '[]');
                            responses[question.id] = values;
                        } else {
                            // Single selection (radio)
                            responses[question.id] = formData.get(question.id) || '';
                        }
                        break;
                        
                    default:
                        responses[question.id] = formData.get(question.id) || '';
                }
            });
            
            // Submit to server
            const response = await fetch(`/api/form/${window.formData.name}/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ responses })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Form submission successful:', data);
                
                // Show success message
                const formContainer = document.querySelector('.public-form-container .public-form');
                const successMessage = document.getElementById('successMessage');
                
                if (formContainer) {
                    formContainer.style.display = 'none';
                }
                
                if (successMessage) {
                    successMessage.style.display = 'block';
                    console.log('Success message should now be visible');
                } else {
                    console.error('Success message element not found');
                }
                
            } else {
                const error = await response.json();
                alert('Error: ' + (error.error || 'Failed to submit form'));
                
                // Reset button
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
            
        } catch (error) {
            console.error('Error submitting form:', error);
            alert('Failed to submit form. Please try again.');
            
            // Reset button
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });
    
    // Add validation for required fields
    const requiredInputs = form.querySelectorAll('input[required]');
    requiredInputs.forEach(input => {
        input.addEventListener('invalid', function(e) {
            e.preventDefault();
            
            // Custom validation message
            if (input.type === 'radio') {
                const questionBlock = input.closest('.question-block');
                const questionTitle = questionBlock.querySelector('.question-title').textContent;
                alert(`Please select an option for: ${questionTitle}`);
            } else {
                const questionBlock = input.closest('.question-block');
                const questionTitle = questionBlock.querySelector('.question-title').textContent;
                alert(`Please fill out: ${questionTitle}`);
            }
        });
    });
});