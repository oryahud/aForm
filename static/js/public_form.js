document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('publicForm');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
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
                if (question.type === 'text') {
                    responses[question.id] = formData.get(question.id) || '';
                } else if (question.type === 'radio') {
                    if (question.multiple) {
                        // Multiple selection (checkboxes)
                        const values = formData.getAll(question.id + '[]');
                        responses[question.id] = values;
                    } else {
                        // Single selection (radio)
                        responses[question.id] = formData.get(question.id) || '';
                    }
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
                // Show success message
                document.querySelector('.public-form-container').style.display = 'none';
                document.getElementById('successMessage').style.display = 'block';
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