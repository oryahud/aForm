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
    
    // Add approval actions if submission is pending
    const status = submission.status || 'pending';
    if (status === 'pending') {
        html += `
            <div class="approval-actions">
                <button class="approve-btn" onclick="approveSubmission('${submission.id}', 'approve')">
                    Approve
                </button>
                <button class="reject-btn" onclick="approveSubmission('${submission.id}', 'reject')">
                    Reject
                </button>
            </div>
        `;
    } else {
        html += `
            <div class="approval-actions">
                <p style="text-align: center; color: #86868b; margin: 0;">
                    This submission has been ${status}
                </p>
            </div>
        `;
    }
    
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

async function approveSubmission(submissionId, action) {
    try {
        const response = await fetch(`/api/form/${window.formData.name}/submission/${submissionId}/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ action })
        });
        
        if (response.ok) {
            // Update the submission in local data
            const submission = window.formData.submissions.find(s => s.id === submissionId);
            if (submission) {
                submission.status = action === 'approve' ? 'approved' : 'rejected';
            }
            
            // Close modal and reload page to update table
            closeSubmissionModal();
            window.location.reload();
        } else {
            const error = await response.json();
            alert('Error: ' + (error.error || 'Failed to update submission'));
        }
    } catch (error) {
        console.error('Error updating submission:', error);
        alert('Failed to update submission. Please try again.');
    }
}

// Initialize share link if present
document.addEventListener('DOMContentLoaded', function() {
    const shareLink = document.getElementById('shareLink');
    if (shareLink) {
        shareLink.value = `${window.location.origin}/submit/${window.formData.name}`;
    }
});