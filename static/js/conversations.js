// JavaScript for Conversation Management Page

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const conversationsContainer = document.getElementById('conversations-container');
    const conversationDetailsContainer = document.getElementById('conversation-details-container');
    const conversationPreview = document.getElementById('conversation-preview');
    const detailConversationTitle = document.getElementById('detail-conversation-title');
    const detailCreatedDate = document.getElementById('detail-created-date');
    const detailUpdatedDate = document.getElementById('detail-updated-date');
    const detailDatasetName = document.getElementById('detail-dataset-name');
    const detailMessageCount = document.getElementById('detail-message-count');
    const noConversations = document.getElementById('no-conversations');
    const paginationContainer = document.getElementById('pagination-container');
    const conversationSearch = document.getElementById('conversation-search');
    const searchBtn = document.getElementById('search-btn');
    const newConversationBtn = document.getElementById('new-conversation-btn');
    const startConversationBtn = document.getElementById('start-conversation-btn');
    const continueConversationBtn = document.getElementById('continue-conversation-btn');
    const exportConversationBtn = document.getElementById('export-conversation-btn');
    const deleteConversationBtn = document.getElementById('delete-conversation-btn');
    const newConversationModal = new bootstrap.Modal(document.getElementById('new-conversation-modal'));
    const newConversationConfirmBtn = document.getElementById('new-conversation-confirm-btn');
    const conversationTitleInput = document.getElementById('conversation-title-input');
    const exportModal = new bootstrap.Modal(document.getElementById('export-modal'));
    const exportConfirmBtn = document.getElementById('export-confirm-btn');
    const exportFormat = document.getElementById('export-format');
    const deleteConfirmModal = new bootstrap.Modal(document.getElementById('delete-confirm-modal'));
    const deleteConfirmBtn = document.getElementById('delete-confirm-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingMessage = document.getElementById('loading-message');
    const darkModeSwitch = document.getElementById('darkModeSwitch');
    
    // State variables
    let conversations = [];
    let currentConversation = null;
    let currentPage = 1;
    let itemsPerPage = 10;
    let totalPages = 1;
    let searchQuery = '';
    let userPreferences = {
        darkMode: localStorage.getItem('darkMode') === 'true',
        fontSize: localStorage.getItem('fontSize') || 'medium'
    };
    
    // Initialise the app
    initialiseUI();
    fetchConversations();
    
    // Event listeners
    if (searchBtn) searchBtn.addEventListener('click', handleSearch);
    if (conversationSearch) conversationSearch.addEventListener('keyup', function(e) {
        if (e.key === 'Enter') handleSearch();
    });
    if (newConversationBtn) newConversationBtn.addEventListener('click', showNewConversationModal);
    if (startConversationBtn) startConversationBtn.addEventListener('click', showNewConversationModal);
    if (newConversationConfirmBtn) newConversationConfirmBtn.addEventListener('click', handleNewConversation);
    if (continueConversationBtn) continueConversationBtn.addEventListener('click', continueConversation);
    if (exportConversationBtn) exportConversationBtn.addEventListener('click', showExportModal);
    if (exportConfirmBtn) exportConfirmBtn.addEventListener('click', handleExport);
    if (deleteConversationBtn) deleteConversationBtn.addEventListener('click', showDeleteConfirmModal);
    if (deleteConfirmBtn) deleteConfirmBtn.addEventListener('click', handleDeleteConversation);
    if (darkModeSwitch) darkModeSwitch.addEventListener('change', toggleDarkMode);
    
    // Initialise UI based on preferences
    function initialiseUI() {
        // Apply dark mode if enabled
        if (userPreferences.darkMode) {
            document.body.setAttribute('data-theme', 'dark');
            darkModeSwitch.checked = true;
        }
        
        // Apply font size
        document.body.setAttribute('data-font-size', userPreferences.fontSize);
    }
    
    // Toggle dark mode
    function toggleDarkMode() {
        const isDarkMode = darkModeSwitch.checked;
        
        if (isDarkMode) {
            document.body.setAttribute('data-theme', 'dark');
        } else {
            document.body.removeAttribute('data-theme');
        }
        
        // Save preference
        userPreferences.darkMode = isDarkMode;
        localStorage.setItem('darkMode', isDarkMode);
    }
    
    // Fetch conversations
    async function fetchConversations() {
        showLoading('Loading conversations...');
        
        try {
            const response = await fetch('/api/conversations');
            const data = await response.json();
            
            if (data.status === 'success') {
                conversations = data.conversations;
                
                if (conversations.length === 0) {
                    showNoConversations();
                } else {
                    displayConversations();
                    setupPagination();
                }
            } else {
                showError('Failed to load conversations');
            }
        } catch (error) {
            console.error('Error:', error);
            showError('Network error. Please try again later.');
        } finally {
            hideLoading();
        }
    }
    
    // Display conversations
    function displayConversations() {
        // Filter conversations by search query if any
        let filteredConversations = conversations;
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            filteredConversations = conversations.filter(conv => 
                conv.title.toLowerCase().includes(query)
            );
        }
        
        // Calculate pagination
        totalPages = Math.ceil(filteredConversations.length / itemsPerPage);
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = Math.min(startIndex + itemsPerPage, filteredConversations.length);
        const paginatedConversations = filteredConversations.slice(startIndex, endIndex);
        
        if (filteredConversations.length === 0) {
            conversationsContainer.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    No conversations found matching your search criteria.
                </div>
            `;
            noConversations.style.display = 'none';
            conversationDetailsContainer.style.display = 'none';
            return;
        }
        
        noConversations.style.display = 'none';
        
        const html = paginatedConversations.map(conv => {
            const createdDate = new Date(conv.created_at).toLocaleString();
            const updatedDate = new Date(conv.updated_at).toLocaleString();
            
            return `
                <div class="conversation-item" data-id="${conv.id}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <div class="conversation-title">${escapeHtml(conv.title)}</div>
                            <div class="conversation-meta">
                                <span><i class="bi bi-clock me-1"></i>${updatedDate}</span> • 
                                <span><i class="bi bi-chat-text me-1"></i>${conv.message_count} messages</span>
                            </div>
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary view-conversation-btn" 
                                    data-id="${conv.id}" title="View Conversation">
                                <i class="bi bi-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger delete-btn" 
                                    data-id="${conv.id}" title="Delete Conversation">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        conversationsContainer.innerHTML = html;
        
        // Add event listeners for conversation items
        document.querySelectorAll('.view-conversation-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.stopPropagation();
                const convId = this.getAttribute('data-id');
                viewConversation(convId);
            });
        });
        
        document.querySelectorAll('.delete-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.stopPropagation();
                const convId = this.getAttribute('data-id');
                confirmDeleteConversation(convId);
            });
        });
        
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', function() {
                const convId = this.getAttribute('data-id');
                viewConversation(convId);
            });
        });
    }
    
    // Setup pagination
    function setupPagination() {
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }
        
        let html = '<nav><ul class="pagination">';
        
        // Previous button
        html += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage - 1}" aria-label="Previous">
                    <span aria-hidden="true">&laquo;</span>
                </a>
            </li>
        `;
        
        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            html += `
                <li class="page-item ${currentPage === i ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        }
        
        // Next button
        html += `
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage + 1}" aria-label="Next">
                    <span aria-hidden="true">&raquo;</span>
                </a>
            </li>
        `;
        
        html += '</ul></nav>';
        
        paginationContainer.innerHTML = html;
        
        // Add event listeners for pagination
        document.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const page = parseInt(this.getAttribute('data-page'));
                if (page >= 1 && page <= totalPages) {
                    currentPage = page;
                    displayConversations();
                    setupPagination();
                    window.scrollTo(0, 0);
                }
            });
        });
    }
    
    // Show no conversations message
    function showNoConversations() {
        conversationsContainer.innerHTML = '';
        noConversations.style.display = 'block';
        conversationDetailsContainer.style.display = 'none';
        paginationContainer.innerHTML = '';
    }
    
    // View conversation details
    async function viewConversation(conversationId) {
        showLoading('Loading conversation details...');
        
        try {
            const response = await fetch(`/api/conversations/${conversationId}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                currentConversation = data.conversation;
                displayConversationDetails(currentConversation);
            } else {
                showError(data.message || 'Failed to load conversation details');
            }
        } catch (error) {
            console.error('Error:', error);
            showError('Network error. Please try again later.');
        } finally {
            hideLoading();
        }
    }
    
    // Display conversation details
    function displayConversationDetails(conversation) {
        conversationDetailsContainer.style.display = 'block';
        
        // Update details
        detailConversationTitle.textContent = conversation.title;
        detailCreatedDate.textContent = new Date(conversation.created_at).toLocaleString();
        detailUpdatedDate.textContent = new Date(conversation.updated_at).toLocaleString();
        detailMessageCount.textContent = conversation.messages.length;
        
        // Get dataset info if available
        if (conversation.dataset_id) {
            fetchDatasetInfo(conversation.dataset_id);
        } else {
            detailDatasetName.textContent = 'Default dataset';
        }
        
        // Display conversation preview
        displayConversationPreview(conversation.messages);
    }
    
    // Fetch dataset info
    async function fetchDatasetInfo(datasetId) {
        try {
            const response = await fetch('/api/datasets');
            const data = await response.json();
            
            if (data.status === 'success') {
                const dataset = data.datasets.find(d => d.id === datasetId);
                if (dataset) {
                    detailDatasetName.textContent = dataset.name;
                } else {
                    detailDatasetName.textContent = 'Unknown dataset';
                }
            } else {
                detailDatasetName.textContent = 'Unknown dataset';
            }
        } catch (error) {
            console.error('Error:', error);
            detailDatasetName.textContent = 'Unknown dataset';
        }
    }
    
    // Display conversation preview
    function displayConversationPreview(messages) {
        if (!messages || messages.length === 0) {
            conversationPreview.innerHTML = '<div class="text-muted">No messages in this conversation</div>';
            return;
        }
        
        // Show first 3 and last 2 messages if there are more than 5 messages
        let messagesToShow = messages;
        let hasMore = false;
        
        if (messages.length > 5) {
            messagesToShow = [...messages.slice(0, 3), ...messages.slice(-2)];
            hasMore = true;
        }
        
        // Create preview HTML
        let html = '';
        
        messagesToShow.forEach((message, index) => {
            if (index === 3 && hasMore) {
                html += `<div class="text-center my-3"><em>... ${messages.length - 5} more messages ...</em></div>`;
            }
            
            let roleIcon, roleClass, roleName;
            
            switch (message.role) {
                case 'user':
                    roleIcon = 'bi-person-circle';
                    roleClass = 'question-container';
                    roleName = 'User';
                    break;
                case 'assistant':
                    roleIcon = 'bi-robot';
                    roleClass = 'answer-container';
                    roleName = 'AI Assistant';
                    break;
                case 'system':
                    roleIcon = 'bi-info-circle';
                    roleClass = 'system-message';
                    roleName = 'System';
                    break;
                default:
                    roleIcon = 'bi-chat';
                    roleClass = '';
                    roleName = message.role;
            }
            
            // Truncate content if too long
            let content = message.content;
            if (content.length > 200) {
                content = content.substring(0, 200) + '...';
            }
            
            html += `
                <div class="${roleClass} small">
                    <div class="d-flex align-items-center">
                        <i class="bi ${roleIcon} me-2"></i>
                        <strong>${roleName}</strong>
                        <small class="ms-2 text-muted">${new Date(message.timestamp).toLocaleTimeString()}</small>
                    </div>
                    <div class="mt-1">
                        ${escapeHtml(content)}
                    </div>
                </div>
            `;
        });
        
        conversationPreview.innerHTML = html;
    }
    
    // Handle search
    function handleSearch() {
        searchQuery = conversationSearch.value.trim();
        currentPage = 1; // Reset to first page
        displayConversations();
        setupPagination();
    }
    
    // Show new conversation modal
    function showNewConversationModal() {
        conversationTitleInput.value = `Conversation ${new Date().toLocaleString()}`;
        newConversationModal.show();
    }
    
    // Handle new conversation
    async function handleNewConversation() {
        const title = conversationTitleInput.value.trim() || `Conversation ${new Date().toLocaleString()}`;
        
        showLoading('Creating conversation...');
        newConversationConfirmBtn.disabled = true;
        
        try {
            const response = await fetch('/api/conversations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                newConversationModal.hide();
                
                // Redirect to the conversation page
                window.location.href = `/?conversation=${data.conversation_id}`;
            } else {
                showError(data.message || 'Failed to create conversation');
            }
        } catch (error) {
            console.error('Error:', error);
            showError('Network error. Please try again later.');
        } finally {
            hideLoading();
            newConversationConfirmBtn.disabled = false;
        }
    }
    
    // Continue conversation
    function continueConversation() {
        if (!currentConversation) return;
        window.location.href = `/?conversation=${currentConversation.id}`;
    }
    
    // Show export modal
    function showExportModal() {
        if (!currentConversation) {
            showError('No conversation selected');
            return;
        }
        
        exportModal.show();
    }
    
    // Handle export
    function handleExport() {
        if (!currentConversation) {
            exportModal.hide();
            return;
        }
        
        const format = exportFormat.value;
        
        // Create a download link
        const downloadLink = document.createElement('a');
        downloadLink.href = `/api/conversations/${currentConversation.id}/export?format=${format}`;
        downloadLink.download = `conversation_export.${format}`;
        document.body.appendChild(downloadLink);
        
        // Click the link and remove it
        downloadLink.click();
        document.body.removeChild(downloadLink);
        
        // Hide modal
        exportModal.hide();
    }
    
    // Show delete confirmation modal
    function showDeleteConfirmModal() {
        if (!currentConversation) {
            showError('No conversation selected');
            return;
        }
        
        deleteConfirmModal.show();
    }
    
    // Confirm delete conversation
    function confirmDeleteConversation(conversationId) {
        // Store the ID to delete
        currentConversation = { id: conversationId };
        
        // Show confirmation modal
        deleteConfirmModal.show();
    }
    
    // Handle delete conversation
    async function handleDeleteConversation() {
        if (!currentConversation) {
            deleteConfirmModal.hide();
            return;
        }
        
        showLoading('Deleting conversation...');
        deleteConfirmBtn.disabled = true;
        
        try {
            const response = await fetch(`/api/conversations/${currentConversation.id}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Hide modal
                deleteConfirmModal.hide();
                
                // Refresh conversations
                await fetchConversations();
                
                // Clear current conversation
                currentConversation = null;
                conversationDetailsContainer.style.display = 'none';
                
                // Show success message
                showNotification('Conversation deleted successfully', 'success');
            } else {
                showError(data.message || 'Failed to delete conversation');
            }
        } catch (error) {
            console.error('Error:', error);
            showError('Network error. Please try again later.');
        } finally {
            hideLoading();
            deleteConfirmBtn.disabled = false;
        }
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
    
    function showLoading(message) {
        loadingMessage.textContent = message || 'Loading...';
        loadingOverlay.classList.remove('d-none');
    }
    
    function hideLoading() {
        loadingOverlay.classList.add('d-none');
    }
    
    function showError(message) {
        showNotification(message, 'danger');
    }
    
    // Show notification
    function showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} notification fade-in`;
        notification.innerHTML = message;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Position notification
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';
        notification.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 5000);
    }
});