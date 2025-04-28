// JavaScript for Dataset Management Page

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const datasetsContainer = document.getElementById('datasets-container');
    const uploadDatasetBtn = document.getElementById('upload-dataset-btn');
    const uploadDatasetModal = new bootstrap.Modal(document.getElementById('upload-dataset-modal'));
    const uploadDatasetForm = document.getElementById('upload-dataset-form');
    const datasetFileInput = document.getElementById('dataset-file');
    const datasetNameInput = document.getElementById('dataset-name');
    const datasetDescriptionInput = document.getElementById('dataset-description');
    const uploadConfirmBtn = document.getElementById('upload-dataset-confirm-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingMessage = document.getElementById('loading-message');
    const darkModeSwitch = document.getElementById('darkModeSwitch');
    
    // State variables
    let userPreferences = {
        darkMode: localStorage.getItem('darkMode') === 'true',
        fontSize: localStorage.getItem('fontSize') || 'medium'
    };
    
    // Initialise the app
    initialiseUI();
    fetchDatasets();
    
    // Event listeners
    uploadDatasetBtn.addEventListener('click', () => uploadDatasetModal.show());
    uploadConfirmBtn.addEventListener('click', handleUploadDataset);
    datasetFileInput.addEventListener('change', handleFileSelect);
    darkModeSwitch.addEventListener('change', toggleDarkMode);
    
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
    
    // Handle file selection
    function handleFileSelect() {
        const file = datasetFileInput.files[0];
        if (file) {
            // Auto-populate name if empty
            if (!datasetNameInput.value) {
                datasetNameInput.value = file.name.replace(/\.[^/.]+$/, ""); // Remove extension
            }
        }
    }
    
    // Fetch available datasets
    async function fetchDatasets() {
        try {
            const response = await fetch('/api/datasets');
            const data = await response.json();
            
            if (data.status === 'success') {
                displayDatasets(data.datasets, data.current_dataset);
            } else {
                datasetsContainer.innerHTML = `<div class="alert alert-danger">Failed to load datasets</div>`;
            }
        } catch (error) {
            console.error('Error:', error);
            datasetsContainer.innerHTML = `<div class="alert alert-danger">Network error</div>`;
        }
    }
    
    // Display datasets
    function displayDatasets(datasets, currentDataset) {
        if (!datasets || datasets.length === 0) {
            datasetsContainer.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    No custom datasets available. Upload a dataset to get started.
                </div>
            `;
            return;
        }
        
        const currentId = currentDataset ? currentDataset.id : null;
        
        const html = datasets.map(dataset => {
            const isActive = dataset.id === currentId;
            const dateAdded = new Date(dataset.date_added).toLocaleDateString();
            const lastUsed = dataset.last_used 
                ? new Date(dataset.last_used).toLocaleDateString() 
                : 'Never';
            
            return `
                <div class="dataset-item ${isActive ? 'active' : ''}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <div class="dataset-title">${escapeHtml(dataset.name)}</div>
                            <div class="dataset-description">${escapeHtml(dataset.description || '')}</div>
                            <div class="dataset-meta">
                                <span>Added: ${dateAdded}</span> • 
                                <span>Last used: ${lastUsed}</span>
                            </div>
                        </div>
                        <div class="btn-group">
                            ${!isActive ? `
                            <button class="btn btn-sm btn-outline-primary activate-dataset-btn" 
                                    data-id="${dataset.id}" title="Activate Dataset">
                                <i class="bi bi-check-lg"></i> Use
                            </button>
                            ` : `
                            <button class="btn btn-sm btn-outline-success" disabled>
                                <i class="bi bi-check-circle-fill"></i> Active
                            </button>
                            `}
                            <button class="btn btn-sm btn-outline-danger delete-dataset-btn" 
                                    data-id="${dataset.id}" title="Delete Dataset">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        datasetsContainer.innerHTML = html;
        
        // Add event listeners for dataset buttons
        document.querySelectorAll('.activate-dataset-btn').forEach(button => {
            button.addEventListener('click', function() {
                const datasetId = this.getAttribute('data-id');
                activateDataset(datasetId);
            });
        });
        
        document.querySelectorAll('.delete-dataset-btn').forEach(button => {
            button.addEventListener('click', function() {
                const datasetId = this.getAttribute('data-id');
                deleteDataset(datasetId);
            });
        });
    }
    
    // Upload a new dataset
    async function handleUploadDataset() {
        // Validate form
        if (!uploadDatasetForm.checkValidity()) {
            uploadDatasetForm.reportValidity();
            return;
        }
        
        const formData = new FormData();
        formData.append('file', datasetFileInput.files[0]);
        formData.append('name', datasetNameInput.value);
        formData.append('description', datasetDescriptionInput.value);
        
        // Show loading overlay
        loadingMessage.textContent = 'Uploading dataset...';
        loadingOverlay.classList.remove('d-none');
        uploadConfirmBtn.disabled = true;
        
        try {
            const response = await fetch('/api/datasets', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Reset form
                uploadDatasetForm.reset();
                
                // Hide modal
                uploadDatasetModal.hide();
                
                // Show success message
                showNotification('Dataset uploaded successfully', 'success');
                
                // Refresh datasets list
                fetchDatasets();
            } else {
                showNotification(data.message || 'Failed to upload dataset', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Network error. Please try again later.', 'error');
        } finally {
            // Hide loading overlay
            loadingOverlay.classList.add('d-none');
            uploadConfirmBtn.disabled = false;
        }
    }
    
    // Activate a dataset
    async function activateDataset(datasetId) {
        // Show loading overlay
        loadingMessage.textContent = 'Activating dataset...';
        loadingOverlay.classList.remove('d-none');
        
        try {
            const response = await fetch(`/api/datasets/${datasetId}/activate`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Show success message
                showNotification('Dataset activated successfully', 'success');
                
                // Refresh datasets list
                fetchDatasets();
            } else {
                showNotification(data.message || 'Failed to activate dataset', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Network error. Please try again later.', 'error');
        } finally {
            // Hide loading overlay
            loadingOverlay.classList.add('d-none');
        }
    }
    
    // Delete a dataset
    async function deleteDataset(datasetId) {
        if (!confirm('Are you sure you want to delete this dataset? This action cannot be undone.')) {
            return;
        }
        
        // Show loading overlay
        loadingMessage.textContent = 'Deleting dataset...';
        loadingOverlay.classList.remove('d-none');
        
        try {
            const response = await fetch(`/api/datasets/${datasetId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Show success message
                showNotification('Dataset deleted successfully', 'success');
                
                // Refresh datasets list
                fetchDatasets();
            } else {
                showNotification(data.message || 'Failed to delete dataset', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Network error. Please try again later.', 'error');
        } finally {
            // Hide loading overlay
            loadingOverlay.classList.add('d-none');
        }
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
});