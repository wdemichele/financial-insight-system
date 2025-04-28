// JavaScript for Hypothesis Testing Page

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const generateBtn = document.getElementById('generate-btn');
    const resetBtn = document.getElementById('reset-btn');
    const datasetInfo = document.getElementById('dataset-info');
    const hypothesesContainer = document.getElementById('hypotheses-container');
    const noHypotheses = document.getElementById('no-hypotheses');
    const hypothesesList = document.getElementById('hypotheses-list');
    const testingResultsContainer = document.getElementById('testing-results-container');
    const testingResults = document.getElementById('testing-results');
    const insightsContainer = document.getElementById('insights-container');
    const insightsContent = document.getElementById('insights-content');
    const exportInsightsBtn = document.getElementById('export-insights-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingMessage = document.getElementById('loading-message');
    const darkModeSwitch = document.getElementById('darkModeSwitch');
    
    // Modals
    const testConfirmModal = new bootstrap.Modal(document.getElementById('test-confirm-modal'));
    const testConfirmBtn = document.getElementById('test-confirm-btn');
    const exportModal = new bootstrap.Modal(document.getElementById('export-modal'));
    const exportConfirmBtn = document.getElementById('export-confirm-btn');
    
    // State variables
    let userPreferences = {
        darkMode: localStorage.getItem('darkMode') === 'true',
        fontSize: localStorage.getItem('fontSize') || 'medium'
    };
    
    let hypotheses = [];
    let testedHypotheses = [];
    let currentHypothesis = null;
    let synthesizedInsights = null;
    
    // Initialise the app
    initialiseUI();
    loadDatasetInfo();
    
    // Event listeners
    generateBtn.addEventListener('click', handleGenerateHypotheses);
    resetBtn.addEventListener('click', handleReset);
    exportInsightsBtn.addEventListener('click', () => exportModal.show());
    exportConfirmBtn.addEventListener('click', handleExportInsights);
    testConfirmBtn.addEventListener('click', handleTestHypothesis);
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
    
    // Load dataset info
    async function loadDatasetInfo() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            if (data.status === 'success') {
                displayDatasetInfo(data.stats);
            } else {
                datasetInfo.innerHTML = `<div class="alert alert-danger">Failed to load dataset information</div>`;
            }
        } catch (error) {
            console.error('Error:', error);
            datasetInfo.innerHTML = `<div class="alert alert-danger">Network error when loading dataset information</div>`;
        }
    }
    
    // Display dataset info
    function displayDatasetInfo(stats) {
        const formatter = new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            maximumFractionDigits: 0
        });
        
        let datasetName = 'Default dataset';
        let datasetDescription = '';
        
        if (stats.current_dataset) {
            datasetName = stats.current_dataset.name;
            datasetDescription = stats.current_dataset.description || '';
        }
        
        const html = `
            <h5>${escapeHtml(datasetName)}</h5>
            <p class="text-muted">${escapeHtml(datasetDescription)}</p>
            <div class="row mt-3">
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-label">Total Records</div>
                        <div class="stat-value">${stats.total_rows.toLocaleString()}</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-label">Total Sales</div>
                        <div class="stat-value">${formatter.format(stats.total_sales)}</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-label">Total Profit</div>
                        <div class="stat-value">${formatter.format(stats.total_profit)}</div>
                    </div>
                </div>
            </div>
        `;
        
        datasetInfo.innerHTML = html;
    }
    
    // Handle generate hypotheses button click
    async function handleGenerateHypotheses() {
        // Show loading overlay
        loadingMessage.textContent = 'Generating hypotheses...';
        loadingOverlay.classList.remove('d-none');
        generateBtn.disabled = true;
        
        try {
            const response = await fetch('/api/generate_hypotheses', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                hypotheses = data.hypotheses;
                displayHypotheses(hypotheses);
                
                // Hide no hypotheses message
                noHypotheses.style.display = 'none';
                // Show hypotheses list
                hypothesesList.style.display = 'block';
            } else {
                showNotification(data.message || 'Failed to generate hypotheses', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Network error. Please try again later.', 'error');
        } finally {
            // Hide loading overlay
            loadingOverlay.classList.add('d-none');
            generateBtn.disabled = false;
        }
    }
    
    // Display hypotheses
    function displayHypotheses(hypotheses) {
        const html = hypotheses.map((hypothesis, index) => {
            const isAlreadyTested = testedHypotheses.some(h => h.id === hypothesis.id);
            
            return `
                <div class="hypothesis-card mb-4 p-3 border rounded ${isAlreadyTested ? 'border-success' : ''}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h5 class="mb-2">Hypothesis ${index + 1}: ${escapeHtml(hypothesis.title)}</h5>
                            <p>${escapeHtml(hypothesis.description)}</p>
                            <div class="mb-2">
                                <span class="badge bg-${getImportanceBadgeColor(hypothesis.importance)}">${hypothesis.importance} Importance</span>
                                <span class="small text-muted ms-2">Confidence: ${hypothesis.confidence || 'Medium'}</span>
                            </div>
                        </div>
                        <div>
                            ${
                                isAlreadyTested ? 
                                `<button class="btn btn-outline-success btn-sm" disabled>
                                    <i class="bi bi-check-circle"></i> Tested
                                </button>` : 
                                `<button class="btn btn-outline-primary btn-sm test-hypothesis-btn" data-hypothesis-id="${hypothesis.id}">
                                    <i class="bi bi-microscope"></i> Test
                                </button>`
                            }
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        hypothesesList.innerHTML = html;
        
        // Add event listeners to test buttons
        document.querySelectorAll('.test-hypothesis-btn').forEach(button => {
            button.addEventListener('click', (event) => {
                const hypothesisId = event.currentTarget.getAttribute('data-hypothesis-id');
                confirmTestHypothesis(hypothesisId);
            });
        });
    }
    
    // Get badge color based on importance
    function getImportanceBadgeColor(importance) {
        switch (importance.toLowerCase()) {
            case 'high':
                return 'danger';
            case 'medium':
                return 'warning';
            case 'low':
                return 'info';
            default:
                return 'secondary';
        }
    }
    
    // Confirm test hypothesis
    function confirmTestHypothesis(hypothesisId) {
        currentHypothesis = hypotheses.find(h => h.id === hypothesisId);
        
        if (!currentHypothesis) {
            showNotification('Hypothesis not found', 'error');
            return;
        }
        
        testConfirmModal.show();
    }
    
    // Handle test hypothesis
    async function handleTestHypothesis() {
        if (!currentHypothesis) {
            showNotification('No hypothesis selected', 'error');
            return;
        }
        
        // Hide modal
        testConfirmModal.hide();
        
        // Show loading overlay
        loadingMessage.textContent = 'Testing hypothesis...';
        loadingOverlay.classList.remove('d-none');
        
        try {
            const response = await fetch('/api/test_hypothesis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    hypothesis_id: currentHypothesis.id,
                    hypothesis_text: currentHypothesis.description
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Add to tested hypotheses
                testedHypotheses.push({
                    ...currentHypothesis,
                    result: data.result
                });
                
                // Display test results
                displayTestResult(currentHypothesis, data.result);
                
                // Update hypotheses display
                displayHypotheses(hypotheses);
                
                // Check if we have enough tested hypotheses to synthesize insights
                if (testedHypotheses.length >= 2) {
                    await synthesizeInsights();
                }
            } else {
                showNotification(data.message || 'Failed to test hypothesis', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Network error. Please try again later.', 'error');
        } finally {
            // Hide loading overlay
            loadingOverlay.classList.add('d-none');
            
            // Reset current hypothesis
            currentHypothesis = null;
        }
    }
    
    // Display test result
    function displayTestResult(hypothesis, result) {
        // Create result container if it doesn't exist
        if (!document.getElementById(`result-${hypothesis.id}`)) {
            const resultHtml = `
                <div id="result-${hypothesis.id}" class="test-result mb-4">
                    <h5>Test Results: ${escapeHtml(hypothesis.title)}</h5>
                    <div class="result-content p-3 border rounded">
                        ${marked.parse(result)}
                    </div>
                </div>
            `;
            
            testingResults.innerHTML += resultHtml;
        }
        
        // Show results container
        testingResultsContainer.style.display = 'block';
        
        // Scroll to results
        testingResultsContainer.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Synthesize insights
    async function synthesizeInsights() {
        // Show loading overlay
        loadingMessage.textContent = 'Synthesizing insights...';
        loadingOverlay.classList.remove('d-none');
        
        try {
            const response = await fetch('/api/synthesize_insights', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    tested_hypotheses: testedHypotheses.map(h => ({
                        id: h.id,
                        title: h.title,
                        description: h.description,
                        result: h.result
                    }))
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Store synthesized insights
                synthesizedInsights = data.insights;
                
                // Display insights
                displayInsights(synthesizedInsights);
            } else {
                showNotification(data.message || 'Failed to synthesize insights', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Network error. Please try again later.', 'error');
        } finally {
            // Hide loading overlay
            loadingOverlay.classList.add('d-none');
        }
    }
    
    // Display insights
    function displayInsights(insights) {
        insightsContent.innerHTML = marked.parse(insights);
        
        // Show insights container
        insightsContainer.style.display = 'block';
        
        // Scroll to insights
        insightsContainer.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Handle reset
    function handleReset() {
        if (confirm('Are you sure you want to reset? This will clear all hypotheses and results.')) {
            // Reset state
            hypotheses = [];
            testedHypotheses = [];
            currentHypothesis = null;
            synthesizedInsights = null;
            
            // Reset UI
            noHypotheses.style.display = 'block';
            hypothesesList.style.display = 'none';
            hypothesesList.innerHTML = '';
            testingResultsContainer.style.display = 'none';
            testingResults.innerHTML = '';
            insightsContainer.style.display = 'none';
            insightsContent.innerHTML = '';
        }
    }
    
    // Handle export insights
    async function handleExportInsights() {
        if (!synthesizedInsights) {
            showNotification('No insights to export', 'warning');
            return;
        }
        
        const format = document.getElementById('export-format').value;
        
        // Hide modal
        exportModal.hide();
        
        // Show loading overlay
        loadingMessage.textContent = 'Exporting insights...';
        loadingOverlay.classList.remove('d-none');
        
        try {
            const response = await fetch('/api/export_insights', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    insights: synthesizedInsights,
                    format: format
                })
            });
            
            if (response.ok) {
                // If it's json, markdown, or txt, download as file
                if (format === 'json' || format === 'markdown' || format === 'txt' || format === 'html') {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `financial_insights.${format}`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                } else if (format === 'pdf') {
                    // If it's PDF, open in new tab/window
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    window.open(url, '_blank');
                    window.URL.revokeObjectURL(url);
                }
                
                showNotification('Insights exported successfully', 'success');
            } else {
                const data = await response.json();
                showNotification(data.message || 'Failed to export insights', 'error');
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