let formToDelete = null;

function confirmDeleteForm(formName) {
    formToDelete = formName;
    document.getElementById('deleteFormName').textContent = formName;
    document.getElementById('deleteFormModal').className = 'modal show';
}

function closeDeleteModal() {
    formToDelete = null;
    document.getElementById('deleteFormModal').className = 'modal';
}

async function deleteForm() {
    if (!formToDelete) return;
    
    const deleteBtn = document.querySelector('.delete-confirm-btn');
    const originalText = deleteBtn.textContent;
    
    // Show loading state
    deleteBtn.disabled = true;
    deleteBtn.textContent = 'Deleting...';
    
    try {
        const response = await fetch(`/api/form/${formToDelete}/delete`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            // Close modal and reload page
            closeDeleteModal();
            window.location.reload();
        } else {
            const error = await response.json();
            alert('Error: ' + (error.error || 'Failed to delete form'));
            
            // Reset button
            deleteBtn.disabled = false;
            deleteBtn.textContent = originalText;
        }
    } catch (error) {
        console.error('Error deleting form:', error);
        alert('Failed to delete form. Please try again.');
        
        // Reset button
        deleteBtn.disabled = false;
        deleteBtn.textContent = originalText;
    }
}

// Close modal when clicking outside
window.addEventListener('click', function(e) {
    const modal = document.getElementById('deleteFormModal');
    if (e.target === modal) {
        closeDeleteModal();
    }
});

function copyFormLink(button) {
    const input = button.parentElement.querySelector('.share-link-input');
    
    // Select and copy text
    input.select();
    document.execCommand('copy');
    
    // Show feedback
    const originalText = button.textContent;
    button.textContent = 'Copied!';
    button.style.background = '#34c759';
    
    setTimeout(() => {
        button.textContent = originalText;
        button.style.background = '';
    }, 2000);
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeDeleteModal();
    }
});