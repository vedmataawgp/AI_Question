// User interface JavaScript functionality for Q&A System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips and popovers
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss flash messages after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Question form enhancements with advanced features
    var questionForm = document.querySelector('form[action*="ask"]');
    var questionTextarea = document.getElementById('question');
    var languageSelect = document.getElementById('language');
    var submitButton = questionForm ? questionForm.querySelector('button[type="submit"]') : null;
    var detectionTimeout;

    if (questionTextarea && submitButton) {
        // Character counter
        var maxLength = 1000;
        var counterElement = document.createElement('div');
        counterElement.className = 'form-text text-end';
        counterElement.id = 'characterCounter';
        questionTextarea.parentNode.appendChild(counterElement);

        function updateCharacterCounter() {
            var currentLength = questionTextarea.value.length;
            var remaining = maxLength - currentLength;
            counterElement.textContent = `${currentLength}/${maxLength} characters`;
            
            if (remaining < 50) {
                counterElement.className = 'form-text text-end text-warning';
            } else if (remaining < 0) {
                counterElement.className = 'form-text text-end text-danger';
                submitButton.disabled = true;
            } else {
                counterElement.className = 'form-text text-end text-muted';
                submitButton.disabled = false;
            }
        }

        questionTextarea.addEventListener('input', function() {
            updateCharacterCounter();
            detectLanguage(this.value);
        });
        questionTextarea.setAttribute('maxlength', maxLength);
        updateCharacterCounter();

        // Language detection function
        function detectLanguage(text) {
            if (text.length < 10) return;
            
            clearTimeout(detectionTimeout);
            detectionTimeout = setTimeout(function() {
                fetch('/api/language/detect', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: text })
                })
                .then(response => response.json())
                .then(data => {
                    var detectedElement = document.getElementById('languageDetected');
                    if (detectedElement && data.detected_language) {
                        var langName = getLanguageName(data.detected_language);
                        detectedElement.innerHTML = '<i data-feather="globe" width="14" height="14" class="me-1"></i>Detected: ' + langName;
                        feather.replace();
                        
                        // Auto-select detected language if available
                        if (languageSelect && languageSelect.value !== data.detected_language) {
                            var option = languageSelect.querySelector('option[value="' + data.detected_language + '"]');
                            if (option) {
                                languageSelect.value = data.detected_language;
                                languageSelect.classList.add('border-info');
                                setTimeout(function() {
                                    languageSelect.classList.remove('border-info');
                                }, 2000);
                            }
                        }
                    }
                })
                .catch(error => console.log('Language detection failed:', error));
            }, 1000);
        }

        // Language selector handler
        if (languageSelect) {
            languageSelect.addEventListener('change', function() {
                updatePlaceholderText(this.value);
                loadLanguageSpecificSuggestions(this.value);
            });
        }

        // Auto-resize textarea
        function autoResize() {
            questionTextarea.style.height = 'auto';
            questionTextarea.style.height = (questionTextarea.scrollHeight) + 'px';
        }

        questionTextarea.addEventListener('input', autoResize);
        autoResize();

        // Form validation
        questionForm.addEventListener('submit', function(e) {
            var question = questionTextarea.value.trim();
            
            if (question.length < 10) {
                e.preventDefault();
                showUserMessage('Please enter a more detailed question (at least 10 characters).', 'warning');
                questionTextarea.focus();
                return false;
            }

            if (question.length > maxLength) {
                e.preventDefault();
                showUserMessage('Question is too long. Please shorten it.', 'error');
                questionTextarea.focus();
                return false;
            }

            // Show loading state
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Searching for answers...';
        });

        // Question suggestions (simple keyword-based)
        var suggestionKeywords = [
            'how to', 'what is', 'why does', 'when should', 'where can',
            'which one', 'who is', 'can you explain', 'steps to', 'guide for'
        ];

        function showQuestionSuggestions() {
            var currentText = questionTextarea.value.toLowerCase();
            var suggestions = [];

            if (currentText.length > 3) {
                suggestionKeywords.forEach(function(keyword) {
                    if (!currentText.includes(keyword)) {
                        suggestions.push(`Try starting with "${keyword}..."`);
                    }
                });

                if (suggestions.length > 0 && currentText.length < 20) {
                    var suggestionHtml = `
                        <div class="alert alert-info alert-dismissible fade show mt-2" role="alert">
                            <small><strong>Tip:</strong> ${suggestions[0]}</small>
                            <button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button>
                        </div>
                    `;
                    
                    var existingSuggestion = questionTextarea.parentNode.querySelector('.alert-info');
                    if (!existingSuggestion && Math.random() < 0.3) { // Show occasionally
                        questionTextarea.parentNode.insertAdjacentHTML('afterend', suggestionHtml);
                    }
                }
            }
        }

        var suggestionTimer;
        questionTextarea.addEventListener('input', function() {
            clearTimeout(suggestionTimer);
            suggestionTimer = setTimeout(showQuestionSuggestions, 2000);
        });
    }

    // Answer cards animations
    var answerCards = document.querySelectorAll('.card[class*="border-start"]');
    if (answerCards.length > 0) {
        // Animate answer cards on load
        answerCards.forEach(function(card, index) {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(function() {
                card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 150);
        });

        // Copy answer functionality
        answerCards.forEach(function(card) {
            var cardBody = card.querySelector('.card-body');
            if (cardBody) {
                var copyButton = document.createElement('button');
                copyButton.className = 'btn btn-sm btn-outline-secondary position-absolute top-0 end-0 m-2';
                copyButton.innerHTML = '<i data-feather="copy" width="16" height="16"></i>';
                copyButton.setAttribute('data-bs-toggle', 'tooltip');
                copyButton.setAttribute('title', 'Copy answer');
                copyButton.style.opacity = '0.7';

                copyButton.addEventListener('click', function() {
                    var answerText = cardBody.textContent.trim();
                    copyToClipboard(answerText);
                });

                card.style.position = 'relative';
                card.appendChild(copyButton);
                
                // Initialize tooltip for copy button
                new bootstrap.Tooltip(copyButton);
            }
        });
    }

    // Feedback form enhancements
    var feedbackForm = document.querySelector('form[action*="feedback"]');
    if (feedbackForm) {
        var feedbackButtons = feedbackForm.querySelectorAll('button[name="helpful"]');
        
        feedbackButtons.forEach(function(button) {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                var isHelpful = this.value === 'yes';
                var confirmMessage = isHelpful ? 
                    'Thank you! This helps us improve our answers.' : 
                    'Thanks for the feedback. We\'ll work on improving our responses.';
                
                // Visual feedback
                feedbackButtons.forEach(function(btn) {
                    btn.disabled = true;
                });
                
                this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Submitting...';
                
                // Submit after short delay for better UX
                setTimeout(function() {
                    feedbackForm.submit();
                }, 500);
                
                showUserMessage(confirmMessage, 'success');
            });
        });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+Enter or Cmd+Enter to submit question
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && questionTextarea) {
            if (document.activeElement === questionTextarea) {
                e.preventDefault();
                if (questionForm) {
                    questionForm.dispatchEvent(new Event('submit'));
                }
            }
        }

        // Escape to clear question
        if (e.key === 'Escape' && questionTextarea && document.activeElement === questionTextarea) {
            if (questionTextarea.value.length > 0) {
                if (confirm('Clear the current question?')) {
                    questionTextarea.value = '';
                    questionTextarea.dispatchEvent(new Event('input'));
                    questionTextarea.focus();
                }
            }
        }
    });

    // Search history (using localStorage)
    function saveQuestionToHistory(question) {
        if (!question || question.length < 10) return;
        
        var history = getQuestionHistory();
        
        // Remove if already exists
        history = history.filter(function(item) {
            return item.question !== question;
        });
        
        // Add to beginning
        history.unshift({
            question: question,
            timestamp: Date.now(),
            date: new Date().toLocaleDateString()
        });
        
        // Keep only last 10 questions
        history = history.slice(0, 10);
        
        localStorage.setItem('qa_question_history', JSON.stringify(history));
    }

    function getQuestionHistory() {
        try {
            var history = localStorage.getItem('qa_question_history');
            return history ? JSON.parse(history) : [];
        } catch (e) {
            return [];
        }
    }

    function showQuestionHistory() {
        var history = getQuestionHistory();
        if (history.length === 0) return;

        var historyHtml = `
            <div class="card mt-3" id="questionHistory">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">
                        <i data-feather="clock" width="16" height="16" class="me-2"></i>
                        Recent Questions
                    </h6>
                    <button type="button" class="btn-close" onclick="document.getElementById('questionHistory').remove()"></button>
                </div>
                <div class="card-body">
                    ${history.map(function(item, index) {
                        return `
                            <div class="d-flex justify-content-between align-items-center ${index > 0 ? 'border-top pt-2 mt-2' : ''}">
                                <div class="flex-grow-1">
                                    <button type="button" class="btn btn-link text-start p-0 text-decoration-none" 
                                            onclick="useHistoryQuestion('${item.question.replace(/'/g, "\\'")}')">
                                        ${item.question.length > 60 ? item.question.substring(0, 60) + '...' : item.question}
                                    </button>
                                    <br><small class="text-muted">${item.date}</small>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;

        if (questionTextarea && !document.getElementById('questionHistory')) {
            questionTextarea.parentNode.insertAdjacentHTML('afterend', historyHtml);
            feather.replace();
        }
    }

    // Global function for history
    window.useHistoryQuestion = function(question) {
        if (questionTextarea) {
            questionTextarea.value = question;
            questionTextarea.dispatchEvent(new Event('input'));
            questionTextarea.focus();
            document.getElementById('questionHistory').remove();
        }
    };

    // Show history on focus (if textarea is empty)
    if (questionTextarea) {
        questionTextarea.addEventListener('focus', function() {
            if (this.value.trim() === '') {
                setTimeout(showQuestionHistory, 300);
            }
        });

        // Save question when form is submitted
        if (questionForm) {
            questionForm.addEventListener('submit', function() {
                var question = questionTextarea.value.trim();
                saveQuestionToHistory(question);
            });
        }
    }

    // Smooth scrolling for anchor links
    var anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            var targetId = this.getAttribute('href').substring(1);
            var targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Back to top button
    var backToTopButton = document.createElement('button');
    backToTopButton.className = 'btn btn-primary position-fixed bottom-0 end-0 m-3';
    backToTopButton.style.display = 'none';
    backToTopButton.style.zIndex = '1050';
    backToTopButton.innerHTML = '<i data-feather="arrow-up" width="20" height="20"></i>';
    backToTopButton.setAttribute('data-bs-toggle', 'tooltip');
    backToTopButton.setAttribute('title', 'Back to top');
    
    document.body.appendChild(backToTopButton);
    new bootstrap.Tooltip(backToTopButton);
    feather.replace();

    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.style.display = 'block';
        } else {
            backToTopButton.style.display = 'none';
        }
    });

    backToTopButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // Print functionality
    var printButton = document.createElement('button');
    printButton.className = 'btn btn-outline-secondary btn-sm position-fixed';
    printButton.style.bottom = '80px';
    printButton.style.right = '20px';
    printButton.style.display = 'none';
    printButton.style.zIndex = '1049';
    printButton.innerHTML = '<i data-feather="printer" width="16" height="16"></i>';
    printButton.setAttribute('data-bs-toggle', 'tooltip');
    printButton.setAttribute('title', 'Print answers');

    // Show print button only on question results page
    if (document.querySelector('.card[class*="border-start"]')) {
        document.body.appendChild(printButton);
        printButton.style.display = 'block';
        new bootstrap.Tooltip(printButton);
        feather.replace();

        printButton.addEventListener('click', function() {
            window.print();
        });
    }
});

// Enhanced utility functions for advanced features
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function() {
            showUserMessage('Answer copied to clipboard!', 'success');
        }).catch(function() {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function getLanguageName(code) {
    var languages = {
        'en': 'English',
        'es': 'Español',
        'fr': 'Français',
        'de': 'Deutsch',
        'it': 'Italiano',
        'pt': 'Português',
        'zh': '中文',
        'ja': '日本語',
        'ko': '한국어',
        'ar': 'العربية',
        'ru': 'Русский',
        'hi': 'हिन्दी',
        'tr': 'Türkçe',
        'nl': 'Nederlands'
    };
    return languages[code] || code.toUpperCase();
}

function updatePlaceholderText(languageCode) {
    var questionTextarea = document.getElementById('question');
    if (!questionTextarea) return;
    
    var placeholders = {
        'en': 'Type your question here... Be as specific as possible for better results.',
        'es': 'Escribe tu pregunta aquí... Sé lo más específico posible para obtener mejores resultados.',
        'fr': 'Tapez votre question ici... Soyez aussi précis que possible pour de meilleurs résultats.',
        'de': 'Geben Sie hier Ihre Frage ein... Seien Sie so spezifisch wie möglich für bessere Ergebnisse.',
        'it': 'Digita la tua domanda qui... Sii il più specifico possibile per risultati migliori.',
        'pt': 'Digite sua pergunta aqui... Seja o mais específico possível para melhores resultados.',
        'zh': '在此输入您的问题...请尽可能具体以获得更好的结果。'
    };
    
    questionTextarea.placeholder = placeholders[languageCode] || placeholders['en'];
}

function loadLanguageSpecificSuggestions(languageCode) {
    fetch('/api/suggestions/' + languageCode)
        .then(response => response.json())
        .then(suggestions => {
            if (suggestions && suggestions.length > 0) {
                displaySuggestions(suggestions);
            }
        })
        .catch(error => {
            console.log('Failed to load language-specific suggestions:', error);
        });
}

function displaySuggestions(suggestions) {
    var suggestionsList = document.getElementById('suggestionsList');
    if (suggestionsList && suggestions.length > 0) {
        suggestionsList.innerHTML = suggestions.slice(0, 6).map(function(suggestion) {
            return '<button type="button" class="btn btn-outline-secondary btn-sm me-2 mb-2" onclick="fillQuestion(\'' + 
                   suggestion.replace(/'/g, "\\'") + '\')">' + suggestion + '</button>';
        }).join('');
        
        var suggestionsDiv = document.getElementById('suggestions');
        if (suggestionsDiv) {
            suggestionsDiv.style.display = 'block';
        }
    }
}

function fillQuestion(text) {
    var questionTextarea = document.getElementById('question');
    if (questionTextarea) {
        questionTextarea.value = text;
        questionTextarea.focus();
        questionTextarea.dispatchEvent(new Event('input'));
        
        // Hide suggestions
        var suggestionsDiv = document.getElementById('suggestions');
        if (suggestionsDiv) {
            suggestionsDiv.style.display = 'none';
        }
    }
}

function searchExternalSources(query, source) {
    var params = new URLSearchParams({
        q: query,
        source: source || 'all'
    });
    
    return fetch('/api/external/search?' + params.toString())
        .then(response => response.json())
        .then(data => data.results || [])
        .catch(error => {
            console.log('External search failed:', error);
            return [];
        });
}

function analyzeWithTransformer(text) {
    return fetch('/api/transformer/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: text })
    })
    .then(response => response.json())
    .catch(error => {
        console.log('Transformer analysis failed:', error);
        return { analysis: {} };
    });
}

function fallbackCopyToClipboard(text) {
    var textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showUserMessage('Answer copied to clipboard!', 'success');
    } catch (err) {
        showUserMessage('Failed to copy to clipboard', 'error');
    }
    
    document.body.removeChild(textArea);
}

function showUserMessage(message, type = 'info') {
    var alertClass = 'alert-' + (type === 'error' ? 'danger' : type);
    var iconName = type === 'success' ? 'check-circle' : 
                   type === 'error' ? 'alert-circle' : 
                   type === 'warning' ? 'alert-triangle' : 'info';

    var alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show position-fixed" 
             style="top: 20px; right: 20px; z-index: 1060; max-width: 400px;" role="alert">
            <i data-feather="${iconName}" width="16" height="16" class="me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', alertHtml);
    feather.replace();

    // Auto-dismiss after 4 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert.position-fixed');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 4000);
}

function formatDateTime(timestamp) {
    var date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

// Export for global use
window.userUtils = {
    copyToClipboard,
    showUserMessage,
    formatDateTime
};

// Progressive Web App features (if service worker is available)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Register service worker for offline functionality (if implemented)
        // This is placeholder for future PWA features
    });
}

// Accessibility improvements
document.addEventListener('keydown', function(e) {
    // Skip to main content with Tab
    if (e.key === 'Tab' && !e.shiftKey && document.activeElement === document.body) {
        var mainContent = document.querySelector('main');
        if (mainContent) {
            e.preventDefault();
            var skipLink = document.createElement('a');
            skipLink.href = '#main-content';
            skipLink.textContent = 'Skip to main content';
            skipLink.className = 'visually-hidden-focusable';
            skipLink.style.position = 'absolute';
            skipLink.style.top = '10px';
            skipLink.style.left = '10px';
            skipLink.style.zIndex = '9999';
            document.body.insertBefore(skipLink, document.body.firstChild);
            skipLink.focus();
            
            skipLink.addEventListener('click', function(e) {
                e.preventDefault();
                mainContent.focus();
                skipLink.remove();
            });
        }
    }
});

// Performance monitoring (basic)
window.addEventListener('load', function() {
    if ('performance' in window) {
        var loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        if (loadTime > 3000) {
            console.warn('Page load time is slow:', loadTime + 'ms');
        }
    }
});

// Enhanced functions for Hindi content display and extraction support
function showFullContent(index) {
    var fullContentDiv = document.getElementById('fullContent' + index);
    if (fullContentDiv) {
        fullContentDiv.style.display = 'block';
        fullContentDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function hideFullContent(index) {
    var fullContentDiv = document.getElementById('fullContent' + index);
    if (fullContentDiv) {
        fullContentDiv.style.display = 'none';
    }
}

// Auto-detect Hindi content and apply appropriate styling
function applyHindiStyling() {
    document.querySelectorAll('.content-text').forEach(function(element) {
        var text = element.textContent || element.innerText;
        if (text.match(/[कखगघचछजझटठडढतथदधनपफबभमयरलवशषसहा]/)) {
            element.classList.add('hindi-content');
        }
    });
}

// Enhanced question suggestions for Hindi
function getHindiQuestionSuggestions() {
    return [
        "यह कैसे काम करता है?",
        "इसका उपयोग कैसे करें?",
        "मुझे इसकी जानकारी चाहिए।",
        "यह क्या है और कैसे उपयोग करें?",
        "इसके फायदे क्या हैं?",
        "कदम-दर-कदम गाइड दें।"
    ];
}

// Enhanced copy function with better feedback
function copyAnswerText(content, type) {
    copyToClipboard(content);
    var message = type === 'paragraph' ? 'Paragraph copied!' : 
                  type === 'full' ? 'Full content copied!' : 'Content copied!';
    showUserMessage(message, 'success');
}

// Initialize enhanced features when document loads
document.addEventListener('DOMContentLoaded', function() {
    // Apply Hindi styling to existing content
    setTimeout(applyHindiStyling, 100);
    
    // Add copy functionality to extracted paragraphs
    document.querySelectorAll('.extracted-paragraph').forEach(function(para) {
        para.addEventListener('click', function() {
            var text = this.textContent.trim();
            copyAnswerText(text, 'paragraph');
        });
        para.setAttribute('title', 'Click to copy this paragraph');
        para.style.cursor = 'pointer';
    });
});
