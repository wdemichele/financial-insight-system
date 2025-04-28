// Enhanced JavaScript for Cbus Financial Insights Application

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements - Main UI
    const questionForm = document.getElementById('question-form');
    const questionInput = document.getElementById('question-input');
    const askButton = document.getElementById('ask-button');
    const conversationContainer = document.getElementById('conversation-container');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    const initialiseBtn = document.getElementById('initialise-btn');
    const statsContainer = document.getElementById('stats-container');
    const sampleQuestionsContainer = document.getElementById('sample-questions');
    const followUpContainer = document.getElementById('follow-up-container');
    const followUpSuggestions = document.getElementById('follow-up-suggestions');
    const currentDatasetDisplay = document.getElementById('current-dataset');
    const conversationTitle = document.getElementById('conversation-title');
    const clearConversationBtn = document.getElementById('clear-conversation-btn');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const logo = document.getElementById('logo');
    
    // DOM elements - Export modal
    const exportBtn = document.getElementById('export-btn');
    const exportModal = new bootstrap.Modal(document.getElementById('export-modal'));
    const exportConfirmBtn = document.getElementById('export-confirm-btn');
    const exportFormat = document.getElementById('export-format');
    
    // DOM elements - New conversation modal
    const newConversationBtn = document.getElementById('new-conversation-btn');
    const newConversationModal = new bootstrap.Modal(document.getElementById('new-conversation-modal'));
    const newConversationForm = document.getElementById('new-conversation-form');
    const conversationTitleInput = document.getElementById('conversation-title-input');
    const newConversationConfirmBtn = document.getElementById('new-conversation-confirm-btn');
    const recentConversationsContainer = document.getElementById('recent-conversations');
    
    // State variables
    let currentConversationId = null;
    let userPreferences = {
        darkMode: localStorage.getItem('darkMode') === 'true',
        fontSize: localStorage.getItem('fontSize') || 'medium',
        showCharts: localStorage.getItem('showCharts') !== 'false',
        showFollowUp: localStorage.getItem('showFollowUp') !== 'false'
    };
    
    // Initialise the app
    initialiseUI();
    fetchStats();
    fetchSampleQuestions();
    fetchRecentConversations();
    
    // Create sidebar overlay element for mobile
    const sidebarOverlay = document.createElement('div');
    sidebarOverlay.className = 'sidebar-overlay';
    document.body.appendChild(sidebarOverlay);
    
    // Event listeners
    questionForm.addEventListener('submit', handleQuestionSubmit);
    initialiseBtn.addEventListener('click', handleInitialise);
    exportBtn.addEventListener('click', () => exportModal.show());
    exportConfirmBtn.addEventListener('click', handleExport);
    newConversationBtn.addEventListener('click', () => {
        conversationTitleInput.value = `Conversation ${new Date().toLocaleString()}`;
        newConversationModal.show();
    });
    newConversationConfirmBtn.addEventListener('click', handleNewConversation);
    clearConversationBtn.addEventListener('click', handleClearConversation);
    themeToggleBtn.addEventListener('click', toggleDarkMode);
    
    // Mobile menu toggle
    if (menuToggle) {
        menuToggle.addEventListener('click', toggleMobileMenu);
    }
    
    // Sidebar overlay click (to close sidebar on mobile)
    sidebarOverlay.addEventListener('click', closeMobileMenu);
    
    // Initialise UI based on preferences
    function initialiseUI() {
        // Apply dark mode if enabled
        if (userPreferences.darkMode) {
            document.body.setAttribute('data-theme', 'dark');
        }
        
        // Apply font size
        document.body.setAttribute('data-font-size', userPreferences.fontSize);
        
        // Hide follow-up container by default
        if (followUpContainer) {
            followUpContainer.style.display = 'none';
        }
        
        // Focus on the question input
        if (questionInput) {
            setTimeout(() => questionInput.focus(), 0);
        }
    }
    
    // Toggle dark mode
    function toggleDarkMode() {
        const isDarkMode = !userPreferences.darkMode;
        
        if (isDarkMode) {
            document.body.setAttribute('data-theme', 'dark');
            // Apply filter to logo in dark mode
            if (logo) logo.classList.add('dark-mode');
        } else {
            document.body.removeAttribute('data-theme');
            // Remove filter from logo in light mode
            if (logo) logo.classList.remove('dark-mode');
        }
        
        // Save preference
        userPreferences.darkMode = isDarkMode;
        localStorage.setItem('darkMode', isDarkMode);
    }
    
    // Toggle mobile menu
    function toggleMobileMenu() {
        sidebar.classList.toggle('show');
        sidebarOverlay.classList.toggle('show');
        document.body.classList.toggle('sidebar-open');
    }
    
    // Close mobile menu
    function closeMobileMenu() {
        sidebar.classList.remove('show');
        sidebarOverlay.classList.remove('show');
        document.body.classList.remove('sidebar-open');
    }
    
    // Submit question when form is submitted
    async function handleQuestionSubmit(event) {
        event.preventDefault();
        
        const question = questionInput.value.trim();
        if (!question) {
            return;
        }
        
        // Clear input and focus
        questionInput.value = '';
        questionInput.focus();
        
        // Show question in conversation
        addQuestionToConversation(question);
        
        // Show loading overlay
        showLoading('Processing your question...');
        askButton.disabled = true;
        
        try {
            // Send question to API
            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question,
                    conversation_id: currentConversationId
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update conversation ID if new conversation was created
                if (currentConversationId !== data.conversation_id) {
                    currentConversationId = data.conversation_id;
                }
                
                // Update conversation title
                refreshConversationTitle();
                
                // Add answer to conversation
                addAnswerToConversation(data.answer, data.processing_time, data.chart_data);
                
                // Show follow-up suggestions if available
                if (data.follow_up_suggestions && data.follow_up_suggestions.length > 0 && userPreferences.showFollowUp) {
                    displayFollowUpSuggestions(data.follow_up_suggestions);
                }
                
                // Refresh recent conversations list
                fetchRecentConversations();
            } else {
                // Show error
                addErrorToConversation(data.message || 'An error occurred while processing your question.');
            }
        } catch (error) {
            console.error('Error:', error);
            addErrorToConversation('Network error. Please try again later.');
        } finally {
            // Hide loading overlay
            hideLoading();
            askButton.disabled = false;
        }
    }
    
    // Re-initialise the system
    async function handleInitialise() {
        // Show loading overlay
        showLoading('Initialising system...');
        initialiseBtn.disabled = true;
        
        try {
            const response = await fetch('/api/initialise', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Show success message
                addSystemMessageToConversation('System initialised successfully.');
                
                // Refresh stats
                fetchStats();
                
                // Refresh sample questions
                fetchSampleQuestions();
                
                // Show success notification
                showNotification('System initialised successfully', 'success');
            } else {
                // Show error
                addErrorToConversation(data.message || 'Failed to initialise system.');
                showNotification('Initialisation failed', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            addErrorToConversation('Network error. Please try again later.');
            showNotification('Network error', 'error');
        } finally {
            // Hide loading overlay
            hideLoading();
            initialiseBtn.disabled = false;
        }
    }
    
    // Create a new conversation
    async function handleNewConversation() {
        const title = conversationTitleInput.value.trim() || `Conversation ${new Date().toLocaleString()}`;
        
        // Show loading overlay
        showLoading('Creating conversation...');
        newConversationConfirmBtn.disabled = true;
        
        try {
            const response = await fetch('/api/conversations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update current conversation ID
                currentConversationId = data.conversation_id;
                
                // Update conversation title
                conversationTitle.textContent = title;
                
                // Clear conversation container
                clearConversation();
                
                // Hide modal
                newConversationModal.hide();
                
                // Refresh recent conversations list
                fetchRecentConversations();
                
                // Show success notification
                showNotification('New conversation created', 'success');
            } else {
                showNotification('Error creating conversation: ' + (data.message || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Network error. Please try again later.', 'error');
        } finally {
            // Hide loading overlay
            hideLoading();
            newConversationConfirmBtn.disabled = false;
        }
    }
    
    // Clear the current conversation
    function handleClearConversation() {
        const confirmClear = confirm('Are you sure you want to clear this conversation? This will only clear the display, not delete the conversation history.');
        if (confirmClear) {
            clearConversation();
            showNotification('Conversation cleared', 'info');
        }
    }
    
    // Clear conversation display
    function clearConversation() {
        conversationContainer.innerHTML = `
            <div class="empty-conversation" id="empty-conversation">
                <div class="empty-icon">
                    <i class="bi bi-chat-square-text"></i>
                </div>
                <p class="empty-text">Ask a question to start the conversation</p>
            </div>
        `;
        
        // Hide follow-up suggestions
        if (followUpContainer) {
            followUpContainer.style.display = 'none';
        }
    }
    
    // Export the current conversation
    async function handleExport() {
        if (!currentConversationId) {
            showNotification('No active conversation to export', 'warning');
            exportModal.hide();
            return;
        }
        
        const format = exportFormat.value;
        
        // Create a download link
        const downloadLink = document.createElement('a');
        downloadLink.href = `/api/conversations/${currentConversationId}/export?format=${format}`;
        downloadLink.download = `conversation_export.${format}`;
        document.body.appendChild(downloadLink);
        
        // Click the link and remove it
        downloadLink.click();
        document.body.removeChild(downloadLink);
        
        // Hide modal
        exportModal.hide();
        
        // Show notification
        showNotification(`Conversation exported as ${format.toUpperCase()}`, 'success');
    }
    
    // Display follow-up suggestions
    function displayFollowUpSuggestions(suggestions) {
        if (!followUpSuggestions || !followUpContainer) return;
        
        followUpSuggestions.innerHTML = '';
        
        suggestions.forEach(suggestion => {
            const suggestionElement = document.createElement('button');
            suggestionElement.className = 'follow-up-suggestion';
            suggestionElement.textContent = suggestion;
            
            // Add click event to use the suggestion
            suggestionElement.addEventListener('click', () => {
                questionInput.value = suggestion;
                questionInput.focus();
                
                // Smooth scroll to question input
                questionInput.scrollIntoView({ behavior: 'smooth' });
            });
            
            followUpSuggestions.appendChild(suggestionElement);
        });
        
        // Show the container
        followUpContainer.style.display = 'block';
    }
    
    // Add question to conversation
    function addQuestionToConversation(question) {
        // Clear the empty state if it exists
        const emptyState = document.getElementById('empty-conversation');
        if (emptyState) {
            emptyState.remove();
        }
        
        const questionHtml = `
            <div class="question-container">
                <div class="question-header">
                    <div class="question-icon">
                        <i class="bi bi-person-circle"></i>
                    </div>
                    <div class="question-title">
                        <strong>You</strong>
                    </div>
                </div>
                <div class="question-content">
                    ${escapeHtml(question)}
                </div>
            </div>
        `;
        
        conversationContainer.innerHTML += questionHtml;
        scrollToBottom();
    }
    
    // Add answer to conversation
    function addAnswerToConversation(answer, processingTime, chartData) {
        // Parse markdown
        const parsedAnswer = marked.parse(answer);
        
        let chartHtml = '';
        if (chartData && userPreferences.showCharts) {
            if (chartData.chart_type === 'base64_image') {
                chartHtml = `
                    <div class="chart-container">
                        <h5 class="chart-title">${chartData.title || 'Chart'}</h5>
                        <img src="data:image/png;base64,${chartData.image_data}" 
                             alt="Data visualization" style="max-width: 100%;" />
                    </div>
                `;
            }
        }
        
        const answerHtml = `
            <div class="answer-container">
                <div class="answer-header">
                    <div class="answer-icon">
                        <i class="bi bi-robot"></i>
                    </div>
                    <div class="answer-title">
                        <strong>Cbus Financial Insights</strong>
                    </div>
                </div>
                <div class="answer-content">
                    ${parsedAnswer}
                    ${chartHtml}
                </div>
                <div class="processing-time">
                    Processed in ${processingTime} seconds
                </div>
            </div>
        `;
        
        conversationContainer.innerHTML += answerHtml;
        scrollToBottom();
    }
    
    // Add error message to conversation
    function addErrorToConversation(errorMessage) {
        const errorHtml = `
            <div class="answer-container" style="border-left-color: var(--danger-color);">
                <div class="answer-header">
                    <div class="answer-icon" style="color: var(--danger-color);">
                        <i class="bi bi-exclamation-triangle"></i>
                    </div>
                    <div class="answer-title">
                        <strong>Error</strong>
                    </div>
                </div>
                <div class="answer-content">
                    ${escapeHtml(errorMessage)}
                </div>
            </div>
        `;
        
        conversationContainer.innerHTML += errorHtml;
        scrollToBottom();
    }
    
    // Add system message to conversation
    function addSystemMessageToConversation(message) {
        const messageHtml = `
            <div class="system-message">
                <div class="d-flex align-items-center">
                    <i class="bi bi-info-circle me-2"></i>
                    <strong>System:</strong>
                </div>
                <div class="mt-2">
                    ${escapeHtml(message)}
                </div>
            </div>
        `;
        
        conversationContainer.innerHTML += messageHtml;
        scrollToBottom();
    }
    
    // Fetch statistics
    async function fetchStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            if (data.status === 'success') {
                displayStats(data.stats);
            } else {
                statsContainer.innerHTML = `<div class="alert alert-danger">Failed to load statistics</div>`;
            }
        } catch (error) {
            console.error('Error:', error);
            statsContainer.innerHTML = `<div class="alert alert-danger">Network error</div>`;
        }
    }
    
    // Display statistics
    function displayStats(stats) {
        const formatter = new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            maximumFractionDigits: 0
        });
        
        // Display current dataset info
        if (stats.current_dataset) {
            currentDatasetDisplay.innerHTML = `
                <strong>${escapeHtml(stats.current_dataset.name)}</strong>
                <div class="text-muted small">${escapeHtml(stats.current_dataset.description || '')}</div>
            `;
        } else {
            currentDatasetDisplay.innerHTML = `<em class="text-muted">Default dataset</em>`;
        }
        
        const html = `
            <div class="stat-card">
                <div class="stat-label">Total Records</div>
                <div class="stat-value">${stats.total_rows.toLocaleString()}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Sales</div>
                <div class="stat-value">${formatter.format(stats.total_sales)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Profit</div>
                <div class="stat-value">${formatter.format(stats.total_profit)}</div>
            </div>
        `;
        
        statsContainer.innerHTML = html;
    }
    
    // Fetch sample questions
    async function fetchSampleQuestions() {
        try {
            const response = await fetch('/api/sample_questions');
            const data = await response.json();
            
            if (data.status === 'success') {
                displaySampleQuestions(data.questions);
            } else {
                sampleQuestionsContainer.innerHTML = `<div class="alert alert-danger">Failed to load sample questions</div>`;
            }
        } catch (error) {
            console.error('Error:', error);
            sampleQuestionsContainer.innerHTML = `<div class="alert alert-danger">Network error</div>`;
        }
    }
    
    // Display sample questions
    function displaySampleQuestions(questions) {
        // Show only the first 5 questions to save space
        const displayQuestions = questions.slice(0, 5);
        
        const html = displayQuestions.map(question => {
            return `
                <div class="sample-question" data-question="${escapeHtml(question)}">
                    ${escapeHtml(question)}
                </div>
            `;
        }).join('');
        
        sampleQuestionsContainer.innerHTML = html;
        
        // Add click events to sample questions
        document.querySelectorAll('.sample-question').forEach(element => {
            element.addEventListener('click', function() {
                const question = this.getAttribute('data-question');
                questionInput.value = question;
                questionInput.focus();
                
                // Close mobile menu if open
                closeMobileMenu();
            });
        });
    }
    
    // Fetch recent conversations
    async function fetchRecentConversations() {
        try {
            const response = await fetch('/api/conversations');
            const data = await response.json();
            
            if (data.status === 'success') {
                displayRecentConversations(data.conversations, data.current_conversation_id);
                
                // Update current conversation ID if not set
                if (!currentConversationId && data.current_conversation_id) {
                    currentConversationId = data.current_conversation_id;
                    refreshConversationTitle();
                }
            } else {
                recentConversationsContainer.innerHTML = `<div class="text-muted text-center py-3">Failed to load conversations</div>`;
            }
        } catch (error) {
            console.error('Error:', error);
            recentConversationsContainer.innerHTML = `<div class="text-muted text-center py-3">Network error</div>`;
        }
    }
    
    // Display recent conversations
    function displayRecentConversations(conversations, currentId) {
        if (!conversations || conversations.length === 0) {
            recentConversationsContainer.innerHTML = `
                <div class="text-muted text-center py-3">
                    <em>No conversations yet</em>
                </div>
            `;
            return;
        }
        
        // Display most recent 3 conversations
        const recentConvs = conversations.slice(0, 3);
        
        const html = recentConvs.map(conv => {
            const isActive = conv.id === currentId;
            const date = new Date(conv.updated_at).toLocaleDateString();
            
            return `
                <div class="conversation-item ${isActive ? 'active' : ''}" data-id="${conv.id}">
                    <div class="conversation-title">${escapeHtml(conv.title)}</div>
                    <div class="conversation-meta">
                        <span>${date}</span> • <span>${conv.message_count} messages</span>
                    </div>
                </div>
            `;
        }).join('');
        
        recentConversationsContainer.innerHTML = html;
        
        // Add click events to conversation items
        document.querySelectorAll('.conversation-item').forEach(element => {
            element.addEventListener('click', function() {
                const convId = this.getAttribute('data-id');
                loadConversation(convId);
                
                // Close mobile menu if open
                closeMobileMenu();
            });
        });
    }
    
    // Load a conversation
    async function loadConversation(conversationId) {
        // Show loading overlay
        showLoading('Loading conversation...');
        
        try {
            const response = await fetch(`/api/conversations/${conversationId}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update current conversation ID
                currentConversationId = conversationId;
                
                // Update conversation title
                conversationTitle.textContent = data.conversation.title;
                
                // Display messages
                displayConversationMessages(data.conversation.messages);
                
                // Activate the conversation
                await fetch(`/api/conversations/${conversationId}/activate`, {
                    method: 'POST'
                });
                
                // Refresh recent conversations list
                fetchRecentConversations();
            } else {
                showNotification('Error loading conversation', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Network error. Please try again later.', 'error');
        } finally {
            // Hide loading overlay
            hideLoading();
        }
    }
    
    // Display conversation messages
    function displayConversationMessages(messages) {
        if (!messages || messages.length === 0) {
            clearConversation();
            return;
        }
        
        conversationContainer.innerHTML = '';
        
        messages.forEach(message => {
            if (message.role === 'user') {
                addQuestionToConversation(message.content);
            } else if (message.role === 'assistant') {
                addAnswerToConversation(
                    message.content, 
                    message.processing_time || 0, 
                    message.chart_data || null
                );
            } else if (message.role === 'system') {
                addSystemMessageToConversation(message.content);
            }
        });
    }
    
    // Refresh conversation title
    async function refreshConversationTitle() {
        if (!currentConversationId) return;
        
        try {
            const response = await fetch(`/api/conversations/${currentConversationId}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                conversationTitle.textContent = data.conversation.title;
            }
        } catch (error) {
            console.error('Error fetching conversation title:', error);
        }
    }
    
    // Loading functions
    function showLoading(message) {
        loadingText.textContent = message || 'Loading...';
        loadingOverlay.classList.remove('d-none');
    }
    
    function hideLoading() {
        loadingOverlay.classList.add('d-none');
    }
    
    // Show notification
    function showNotification(message, type) {
        // Map type to Bootstrap alert class
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert ${alertClass} notification`;
        notification.innerHTML = message;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 4 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 4000);
    }
    
    // Helper functions
    function escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    function scrollToBottom() {
        const scrollHeight = conversationContainer.scrollHeight;
        const height = conversationContainer.clientHeight;
        const maxScrollTop = scrollHeight - height;
        conversationContainer.scrollTop = maxScrollTop > 0 ? maxScrollTop : 0;
    }
});