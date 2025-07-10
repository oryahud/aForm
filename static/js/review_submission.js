async function approveSubmission(action) {
    const approveBtn = document.querySelector('.approve-btn');
    const rejectBtn = document.querySelector('.reject-btn');
    
    // Disable buttons and show loading
    if (approveBtn) approveBtn.disabled = true;
    if (rejectBtn) rejectBtn.disabled = true;
    
    const activeBtn = action === 'approve' ? approveBtn : rejectBtn;
    const originalText = activeBtn.textContent;
    activeBtn.textContent = action === 'approve' ? 'Approving...' : 'Rejecting...';
    
    try {
        const response = await fetch(`/api/form/${window.formName}/submission/${window.submissionData.id}/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ action })
        });
        
        if (response.ok) {
            // Reload page to show updated status
            window.location.reload();
        } else {
            const error = await response.json();
            alert('Error: ' + (error.error || 'Failed to update submission'));
            
            // Reset buttons
            if (approveBtn) {
                approveBtn.disabled = false;
                approveBtn.textContent = '✓ Approve Submission';
            }
            if (rejectBtn) {
                rejectBtn.disabled = false;
                rejectBtn.textContent = '✗ Reject Submission';
            }
        }
    } catch (error) {
        console.error('Error updating submission:', error);
        alert('Failed to update submission. Please try again.');
        
        // Reset buttons
        if (approveBtn) {
            approveBtn.disabled = false;
            approveBtn.textContent = '✓ Approve Submission';
        }
        if (rejectBtn) {
            rejectBtn.disabled = false;
            rejectBtn.textContent = '✗ Reject Submission';
        }
    }
}