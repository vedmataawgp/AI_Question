// Admin panel JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // File upload preview
    var fileInput = document.getElementById('uploadFile');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            var file = e.target.files[0];
            if (file) {
                var fileInfo = document.createElement('div');
                fileInfo.className = 'mt-2 text-muted small';
                fileInfo.innerHTML = `
                    <i data-feather="file" width="16" height="16"></i>
                    ${file.name} (${formatFileSize(file.size)})
                `;
                
                // Remove existing file info
                var existingInfo = fileInput.parentNode.querySelector('.file-info');
                if (existingInfo) {
                    existingInfo.remove();
                }
                
                fileInfo.className += ' file-info';
                fileInput.parentNode.appendChild(fileInfo);
                feather.replace();
            }
        });
    }

    // Confirm delete actions
    var deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            var message = this.getAttribute('data-confirm-delete') || 'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Auto-resize textareas
    var textareas = document.querySelectorAll('textarea');
    textareas.forEach(function(textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });

    // Search functionality for tables
    var searchInput = document.getElementById('tableSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            var searchTerm = this.value.toLowerCase();
            var tableRows = document.querySelectorAll('tbody tr');
            
            tableRows.forEach(function(row) {
                var text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Category filter functionality
    var categoryFilter = document.querySelector('select[name="category"]');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', function() {
            this.form.submit();
        });
    }

    // Bulk action functionality
    var bulkActionForm = document.getElementById('bulkActionForm');
    if (bulkActionForm) {
        var checkboxes = bulkActionForm.querySelectorAll('input[type="checkbox"]');
        var selectAllCheckbox = document.getElementById('selectAll');
        var bulkActionSelect = document.getElementById('bulkAction');
        var bulkActionButton = document.getElementById('bulkActionButton');

        // Select all functionality
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                checkboxes.forEach(function(checkbox) {
                    if (checkbox !== selectAllCheckbox) {
                        checkbox.checked = selectAllCheckbox.checked;
                    }
                });
                updateBulkActionButton();
            });
        }

        // Individual checkbox change
        checkboxes.forEach(function(checkbox) {
            if (checkbox !== selectAllCheckbox) {
                checkbox.addEventListener('change', updateBulkActionButton);
            }
        });

        function updateBulkActionButton() {
            var checkedCount = Array.from(checkboxes).filter(cb => cb !== selectAllCheckbox && cb.checked).length;
            if (bulkActionButton) {
                bulkActionButton.disabled = checkedCount === 0;
                bulkActionButton.textContent = `Apply to ${checkedCount} item(s)`;
            }
        }

        // Bulk action execution
        if (bulkActionButton) {
            bulkActionButton.addEventListener('click', function(e) {
                e.preventDefault();
                var action = bulkActionSelect.value;
                var checkedItems = Array.from(checkboxes).filter(cb => cb !== selectAllCheckbox && cb.checked);
                
                if (checkedItems.length === 0) {
                    alert('Please select at least one item.');
                    return;
                }

                var confirmMessage = `Are you sure you want to ${action} ${checkedItems.length} item(s)?`;
                if (confirm(confirmMessage)) {
                    bulkActionForm.submit();
                }
            });
        }
    }

    // Real-time validation
    var forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(function(form) {
        var inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(function(input) {
            input.addEventListener('blur', validateField);
            input.addEventListener('input', clearValidation);
        });
    });

    function validateField(e) {
        var field = e.target;
        var value = field.value.trim();
        var isValid = true;
        var errorMessage = '';

        // Required field validation
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'This field is required.';
        }

        // Email validation
        if (field.type === 'email' && value) {
            var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address.';
            }
        }

        // URL validation
        if (field.type === 'url' && value) {
            try {
                new URL(value);
            } catch {
                isValid = false;
                errorMessage = 'Please enter a valid URL.';
            }
        }

        // Display validation result
        showFieldValidation(field, isValid, errorMessage);
    }

    function clearValidation(e) {
        var field = e.target;
        field.classList.remove('is-valid', 'is-invalid');
        var feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }

    function showFieldValidation(field, isValid, message) {
        field.classList.remove('is-valid', 'is-invalid');
        
        if (!isValid) {
            field.classList.add('is-invalid');
            var existingFeedback = field.parentNode.querySelector('.invalid-feedback');
            if (existingFeedback) {
                existingFeedback.textContent = message;
            } else {
                var feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.textContent = message;
                field.parentNode.appendChild(feedback);
            }
        } else if (field.value.trim()) {
            field.classList.add('is-valid');
        }
    }
});

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    var k = 1024;
    var sizes = ['Bytes', 'KB', 'MB', 'GB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function() {
            showToast('Copied to clipboard!', 'success');
        });
    } else {
        // Fallback for older browsers
        var textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
            showToast('Copied to clipboard!', 'success');
        } catch (err) {
            showToast('Failed to copy to clipboard', 'error');
        }
        document.body.removeChild(textArea);
    }
}

function showToast(message, type = 'info') {
    var toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    var toastId = 'toast-' + Date.now();
    var toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i data-feather="${getToastIcon(type)}" width="16" height="16" class="me-2"></i>
                <strong class="me-auto">${getToastTitle(type)}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    var toastElement = document.getElementById(toastId);
    var toast = new bootstrap.Toast(toastElement);
    toast.show();

    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });

    feather.replace();
}

function getToastIcon(type) {
    switch (type) {
        case 'success': return 'check-circle';
        case 'error': return 'alert-circle';
        case 'warning': return 'alert-triangle';
        default: return 'info';
    }
}

function getToastTitle(type) {
    switch (type) {
        case 'success': return 'Success';
        case 'error': return 'Error';
        case 'warning': return 'Warning';
        default: return 'Info';
    }
}

// Export functions for global use
window.adminUtils = {
    formatFileSize,
    copyToClipboard,
    showToast
};
