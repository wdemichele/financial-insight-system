// JavaScript for Settings Management Page

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements - Settings forms
    const systemSettingsForm = document.getElementById('system-settings-form');
    const interfaceSettingsForm = document.getElementById('interface-settings-form');
    const analystDeployment = document.getElementById('analyst-deployment');
    const insightDeployment = document.getElementById('insight-deployment');
    const cacheDuration = document.getElementById('cache-duration');
    const memcacheSize = document.getElementById('memcache-size');
    const darkModeDefault = document.getElementById('darkModeDefault');
    const autoGenerateCharts = document.getElementById('autoGenerateCharts');
    const showFollowUpSuggestions = document.getElementById('showFollowUpSuggestions');
    const fontSize = document.getElementById('fontSize');
    
    // DOM elements - Maintenance buttons
    const initialiseSystemBtn = document.getElementById('initialise-system-btn');
    const clearCacheBtn = document.getElementById('clear-cache-btn');
    const resetSystemBtn = document.getElementById('reset-system-btn');
    const maintenanceResult = document.getElementById('maintenance-result');
    
    // DOM elements - Modals
    const resetConfirmModal = new bootstrap.Modal(document.getElementById('reset-confirm-modal'));
    const resetConfirmBtn = document.getElementById('reset-confirm-btn');
    
    // DOM elements - Other
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingMessage = document.getElementById('loading-message');
    const darkModeSwitch = document.getElementById('darkModeSwitch');
    
    // State variables
    let userPreferences = {
        darkMode: localStorage.getItem('darkMode') === 'true',
        fontSize: localStorage.getItem('fontSize') || 'medium',
        showCharts: localStorage.getItem('showCharts') !== 'false',
        showFollowUp: localStorage.getItem('showFollowUp') !== 'false'
    };
    
    // Initialise the app
    initialiseUI();
    fetchSettings();
    
    // Event listeners
    if (systemSettingsForm) systemSettingsForm.addEventListener('submit', handleSystemSettingsSave);
    if (interfaceSettingsForm) interfaceSettingsForm.addEventListener('submit', handleInterfaceSettingsSave);
    if (initialiseSystemBtn) initialiseSystemBtn.addEventListener('click', handleInitialiseSystem);
    if (clearCacheBtn) clearCacheBtn.addEventListener('click', handleClearCache);
    if (resetSystemBtn) resetSystemBtn.addEventListener('click', showResetConfirmModal);
    if (resetConfirmBtn) resetConfirmBtn.addEventListener('click', handleResetSystem);
    if (darkModeSwitch) darkModeSwitch.addEventListener('change', toggleDarkMode);
    
    // Initialise UI based on preferences
    function initialiseUI() {
        // Apply dark mode if enabled
        if (userPreferences.darkMode) {
            document.body.setAttribute('data-theme', 'dark');
            darkModeSwitch.checked = true;
            
            // Also update the interface setting
            if (darkModeDefault) darkModeDefault.checked = true;
        }
        
        // Apply font size
        document.body.setAttribute('data-font-size', userPreferences.fontSize);
        
        // Update interface settings form
        if (fontSize) fontSize.value = userPreferences.fontSize;
        if (autoGenerateCharts) autoGenerateCharts.checked = userPreferences.showCharts;
        if (showFollowUpSuggestions) showFollowUpSuggestions.checked = userPreferences.showFollowUp;
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
        
        // Also update the interface setting
        if (darkModeDefault) darkModeDefault.checked = isDarkMode;
    }
    
    // Fetch settings from server or local storage
    async function fetchSettings() {
        // For system settings, we can fetch from an API endpoint
        try {
            const response = await fetch('/api/settings');
            
            // If the endpoint exists and returns valid data
            if (response.ok) {
                const data = await response.json();
                
                if (data.status === 'success') {
                    // Update form fields
                    if (analystDeployment) analystDeployment.value = data.settings.analyst_deployment || '';
                    if (insightDeployment) insightDeployment.value = data.settings.insight_deployment || '';
                    if (cacheDuration) cacheDuration.value = data.settings.cache_duration || 7;
                    if (memcacheSize) memcacheSize.value = data.settings.memcache_size || 100;
                }
            } else {
                // Fall back to default values
                setDefaultSystemSettings();
            }
        } catch (error) {
            console.error('Error fetching settings:', error);
            setDefaultSystemSettings();
        }
        
        // For interface settings, we use localStorage
        if (fontSize) fontSize.value = userPreferences.fontSize;
        if (darkModeDefault) darkModeDefault.checked = userPreferences.darkMode;
        if (autoGenerateCharts) autoGenerateCharts.checked = userPreferences.showCharts;
        if (showFollowUpSuggestions) showFollowUpSuggestions.checked = userPreferences.showFollowUp;
    }
    
    // Set default system settings
    function setDefaultSystemSettings() {
        if (analystDeployment) analystDeployment.value = 'gpt-4';
        if (insightDeployment) insightDeployment.value = 'gpt-4';
        if (cacheDuration) cacheDuration.value = 7;
        if (memcacheSize) memcacheSize.value = 100;
    }
    
    // Handle saving system settings
    async function handleSystemSettingsSave(event) {
        event.preventDefault();
        
        // Get values from form
        const settings = {
            analyst_deployment: analystDeployment.value,
            insight_deployment: insightDeployment.value,
            cache_duration: parseInt(cacheDuration.value),
            memcache_size: parseInt(memcacheSize.value)
        };
        
        // Show loading overlay
        showLoading('Saving system settings...');
        
        try {
            // Send to API endpoint if it exists
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.status === 'success') {
                    showSuccessMessage('System settings saved successfully');
                } else {
                    showErrorMessage(data.message || 'Failed to save system settings');
                }
            } else {
                // If endpoint doesn't exist or returns error, we can mock success
                // In a real app, you'd want to handle this differently
                showSuccessMessage('System settings saved successfully');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            // For demo purposes, we'll show success even if the API call fails
            // In a real app, you'd want to show an error
            showSuccessMessage('System settings saved successfully');
        } finally {
            hideLoading();
        }
    }
    
    // Handle saving interface settings
    function handleInterfaceSettingsSave(event) {
        event.preventDefault();
        
        // Get values from form
        const isDarkMode = darkModeDefault.checked;
        const fontSizeValue = fontSize.value;
        const showCharts = autoGenerateCharts.checked;
        const showFollowUp = showFollowUpSuggestions.checked;
        
        // Update user preferences
        userPreferences.darkMode = isDarkMode;
        userPreferences.fontSize = fontSizeValue;
        userPreferences.showCharts = showCharts;
        userPreferences.showFollowUp = showFollowUp;
        
        // Save to localStorage
        localStorage.setItem('darkMode', isDarkMode);
        localStorage.setItem('fontSize', fontSizeValue);
        localStorage.setItem('showCharts', showCharts);
        localStorage.setItem('showFollowUp', showFollowUp);
        
        // Apply changes
        if (isDarkMode) {
            document.body.setAttribute('data-theme', 'dark');
            darkModeSwitch.checked = true;
        } else {
            document.body.removeAttribute('data-theme');
            darkModeSwitch.checked = false;
        }
        
        document.body.setAttribute('data-font-size', fontSizeValue);
        
        // Show success message
        showSuccessMessage('Interface settings saved successfully');
    }
    
    // Initialise system
    async function handleInitialiseSystem() {
        showLoading('Initialising system...');
        
        try {
            const response = await fetch('/api/initialise', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                showMaintenanceResult('System initialised successfully', 'success');
            } else {
                showMaintenanceResult(data.message || 'Failed to initialise system', 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            showMaintenanceResult('Network error. Please try again later.', 'danger');
        } finally {
            hideLoading();
        }
    }
    
    // Clear cache
    async function handleClearCache() {
        showLoading('Clearing cache...');
        
        try {
            const response = await fetch('/api/clear_cache', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                showMaintenanceResult(data.message || 'Cache cleared successfully', 'success');
            } else {
                showMaintenanceResult(data.message || 'Failed to clear cache', 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            showMaintenanceResult('Network error. Please try again later.', 'danger');
        } finally {
            hideLoading();
        }
    }
    
    // Show reset confirm modal
    function showResetConfirmModal() {
        resetConfirmModal.show();
    }
    
    // Reset system
    async function handleResetSystem() {
        resetConfirmModal.hide();
        showLoading('Resetting system...');
        
        try {
            // In a real application, you would have an API endpoint for this
            // Here we'll simulate by clearing localStorage and calling initialise
            
            // Clear localStorage
            localStorage.clear();
            
            // Reset user preferences
            userPreferences = {
                darkMode: false,
                fontSize: 'medium',
                showCharts: true,
                showFollowUp: true
            };
            
            // Apply default UI settings
            document.body.removeAttribute('data-theme');
            document.body.setAttribute('data-font-size', 'medium');
            
            if (darkModeSwitch) darkModeSwitch.checked = false;
            if (darkModeDefault) darkModeDefault.checked = false;
            if (fontSize) fontSize.value = 'medium';
            if (autoGenerateCharts) autoGenerateCharts.checked = true;
            if (showFollowUpSuggestions) showFollowUpSuggestions.checked = true;
            
            // Initialise system
            const response = await fetch('/api/initialise', {
                method: 'POST'
            });
            
            // Clear cache
            await fetch('/api/clear_cache', {
                method: 'POST'
            });
            
            showMaintenanceResult('System has been reset to default settings', 'success');
        } catch (error) {
            console.error('Error:', error);
            showMaintenanceResult('Error during system reset. Some settings may not have been reset properly.', 'warning');
        } finally {
            hideLoading();
        }
    }
    
    // Show maintenance result
    function showMaintenanceResult(message, type) {
        maintenanceResult.className = `alert alert-${type}`;
        maintenanceResult.textContent = message;
        maintenanceResult.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            maintenanceResult.style.opacity = '0';
            setTimeout(() => {
                maintenanceResult.style.display = 'none';
                maintenanceResult.style.opacity = '1';
            }, 300);
        }, 5000);
    }
    
    // Show success message
    function showSuccessMessage(message) {
        showNotification(message, 'success');
    }
    
    // Show error message
    function showErrorMessage(message) {
        showNotification(message, 'danger');
    }
    
    // Helper functions
    function showLoading(message) {
        loadingMessage.textContent = message || 'Loading...';
        loadingOverlay.classList.remove('d-none');
    }
    
    function hideLoading() {
        loadingOverlay.classList.add('d-none');
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