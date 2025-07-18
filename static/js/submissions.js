function copyShareLink() {
    const shareUrl = `${window.location.origin}/submit/${window.formData.name}`;
    
    // Create temporary input to copy text
    const tempInput = document.createElement('input');
    tempInput.value = shareUrl;
    document.body.appendChild(tempInput);
    tempInput.select();
    document.execCommand('copy');
    document.body.removeChild(tempInput);
    
    // Show feedback
    const btn = event.target;
    const originalText = btn.textContent;
    btn.textContent = 'Copied!';
    btn.style.background = '#34c759';
    
    setTimeout(() => {
        btn.textContent = originalText;
        btn.style.background = '';
    }, 2000);
}

function viewSubmission(submissionId) {
    const submission = window.formData.submissions.find(s => s.id === submissionId);
    if (!submission) return;
    
    const modal = document.getElementById('submissionModal');
    const detailsContainer = document.getElementById('submissionDetails');
    
    // Format submission date
    const date = new Date(submission.submitted_at);
    const formattedDate = date.toLocaleDateString() + ' at ' + date.toLocaleTimeString();
    
    let html = `
        <div class="submission-meta">
            <h3>Submission ID: ${submission.id}</h3>
            <p>Submitted on ${formattedDate}</p>
        </div>
    `;
    
    // Add each question and answer
    window.formData.questions.forEach(question => {
        const answer = submission.responses[question.id];
        let displayAnswer = '';
        
        if (Array.isArray(answer)) {
            displayAnswer = answer.length > 0 ? answer.join(', ') : 'No selection';
        } else {
            displayAnswer = answer || 'No answer';
        }
        
        html += `
            <div class="submission-detail-item">
                <h4>${question.title}</h4>
                <p>${displayAnswer}</p>
            </div>
        `;
    });
    
    
    detailsContainer.innerHTML = html;
    modal.className = 'modal show';
}

function closeSubmissionModal() {
    document.getElementById('submissionModal').className = 'modal';
}

// Close modal when clicking outside
window.addEventListener('click', function(e) {
    const modal = document.getElementById('submissionModal');
    if (e.target === modal) {
        closeSubmissionModal();
    }
});

// Delete submission function
async function deleteSubmission(submissionId) {
    if (!confirm('Are you sure you want to delete this submission? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/form/${window.formData.name}/submission/${submissionId}/delete`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            // Reload the page to refresh the submissions list
            window.location.reload();
        } else {
            const error = await response.json();
            alert('Error: ' + (error.error || 'Failed to delete submission'));
        }
    } catch (error) {
        console.error('Error deleting submission:', error);
        alert('Failed to delete submission. Please try again.');
    }
}

// Initialize share link if present
document.addEventListener('DOMContentLoaded', function() {
    const shareLink = document.getElementById('shareLink');
    if (shareLink) {
        shareLink.value = `${window.location.origin}/submit/${window.formData.name}`;
    }
});