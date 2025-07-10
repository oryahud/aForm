function openCreateFormModal() {
    const modal = document.getElementById('createFormModal');
    const input = document.getElementById('formNameInput');
    const modalMessage = document.getElementById('modalMessage');
    
    modal.className = 'modal show';
    input.value = '';
    input.focus();
    modalMessage.className = 'message';
    
    // Handle Enter key
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            submitFormCreation();
        }
    });
}

function closeCreateFormModal() {
    const modal = document.getElementById('createFormModal');
    modal.className = 'modal';
}

async function submitFormCreation() {
    const input = document.getElementById('formNameInput');
    const modalMessage = document.getElementById('modalMessage');
    const createButton = document.querySelector('.modal-buttons .create-form-btn');
    
    const formName = input.value.trim();
    
    if (!formName) {
        modalMessage.textContent = 'Please enter a form name.';
        modalMessage.className = 'message error show';
        return;
    }
    
    // Add loading state
    createButton.disabled = true;
    createButton.textContent = 'Creating...';
    
    try {
        const response = await fetch('/create-form', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: formName })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Redirect to the new form page
            window.location.href = data.redirect;
        } else {
            // Show error message
            modalMessage.textContent = data.error;
            modalMessage.className = 'message error show';
            
            // Reset button
            createButton.disabled = false;
            createButton.textContent = 'Create Form';
        }
        
    } catch (error) {
        console.error('Error:', error);
        modalMessage.textContent = 'Something went wrong. Please try again.';
        modalMessage.className = 'message error show';
        
        // Reset button
        createButton.disabled = false;
        createButton.textContent = 'Create Form';
    }
}

// Close modal when clicking outside
window.addEventListener('click', function(e) {
    const modal = document.getElementById('createFormModal');
    if (e.target === modal) {
        closeCreateFormModal();
    }
});