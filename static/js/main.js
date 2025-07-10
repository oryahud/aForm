async function createForm() {
    const button = document.querySelector('.create-form-btn');
    const messageDiv = document.getElementById('message');
    
    // Add loading state
    button.disabled = true;
    button.textContent = 'Creating...';
    
    try {
        const response = await fetch('/create-form', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        // Show success message
        messageDiv.textContent = data.message;
        messageDiv.className = 'message success show';
        
        // Reset button
        button.disabled = false;
        button.textContent = 'Create a New Form';
        
        // Hide message after 3 seconds
        setTimeout(() => {
            messageDiv.className = 'message';
        }, 3000);
        
    } catch (error) {
        console.error('Error:', error);
        messageDiv.textContent = 'Something went wrong. Please try again.';
        messageDiv.className = 'message error show';
        
        // Reset button
        button.disabled = false;
        button.textContent = 'Create a New Form';
    }
}