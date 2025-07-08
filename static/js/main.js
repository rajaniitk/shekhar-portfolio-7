// EDA Pro Main JavaScript Functions

// Global variables
let currentDatasetId = null;
let loadingTimeout = null;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    checkForUpdates();
    initializePage();
    checkConnectivity();
    
    // Add a small delay to ensure everything is loaded
    setTimeout(() => {
        updateCurrentDatasetDisplay();
    }, 500);
});

function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize theme
    initializeTheme();
    
    // Setup CSRF token for AJAX requests
    setupCSRFToken();
    
    // Initialize notification system
    initializeNotifications();
    
    console.log('EDA Pro initialized successfully');
}

function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializeTheme() {
    // Apply dark theme
    document.documentElement.setAttribute('data-bs-theme', 'dark');
    
    // Apply custom theme preferences if stored
    const savedTheme = localStorage.getItem('eda-pro-theme');
    if (savedTheme) {
        applyThemePreferences(JSON.parse(savedTheme));
    }
}

function applyThemePreferences(preferences) {
    if (preferences.primaryColor) {
        document.documentElement.style.setProperty('--primary-color', preferences.primaryColor);
    }
    if (preferences.accentColor) {
        document.documentElement.style.setProperty('--neon-blue', preferences.accentColor);
    }
}

function setupCSRFToken() {
    // Setup CSRF token for AJAX requests if needed
    const token = document.querySelector('meta[name="csrf-token"]');
    if (token) {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", token.getAttribute('content'));
                }
            }
        });
    }
}

function setupEventListeners() {
    // Global keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // Handle file drag and drop
    setupDragAndDrop();
    
    // Auto-save forms
    setupAutoSave();
    
    // Progress tracking
    setupProgressTracking();
}

function handleKeyboardShortcuts(event) {
    // Ctrl+U for upload
    if (event.ctrlKey && event.key === 'u') {
        event.preventDefault();
        window.location.href = '/upload';
    }
    
    // Ctrl+D for dashboard
    if (event.ctrlKey && event.key === 'd') {
        event.preventDefault();
        window.location.href = '/dashboard';
    }
    
    // Ctrl+R for reports
    if (event.ctrlKey && event.key === 'r') {
        event.preventDefault();
        window.location.href = '/reports';
    }
    
    // Escape to close modals
    if (event.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
}

function setupDragAndDrop() {
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        document.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Highlight drop area
    ['dragenter', 'dragover'].forEach(eventName => {
        document.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        document.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight(e) {
        const uploadArea = document.querySelector('.upload-area');
        if (uploadArea) {
            uploadArea.classList.add('drag-over');
        }
    }
    
    function unhighlight(e) {
        const uploadArea = document.querySelector('.upload-area');
        if (uploadArea) {
            uploadArea.classList.remove('drag-over');
        }
    }
    
    // Handle dropped files
    document.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0 && window.location.pathname === '/upload') {
            handleFileSelect(files[0]);
        }
    }
}

function setupAutoSave() {
    // Auto-save form data to localStorage
    const forms = document.querySelectorAll('form[data-autosave]');
    
    forms.forEach(form => {
        const formId = form.getAttribute('data-autosave');
        
        // Load saved data
        const savedData = localStorage.getItem(`autosave-${formId}`);
        if (savedData) {
            const data = JSON.parse(savedData);
            restoreFormData(form, data);
        }
        
        // Save on input
        form.addEventListener('input', debounce(() => {
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            localStorage.setItem(`autosave-${formId}`, JSON.stringify(data));
        }, 1000));
        
        // Clear on submit
        form.addEventListener('submit', () => {
            localStorage.removeItem(`autosave-${formId}`);
        });
    });
}

function restoreFormData(form, data) {
    Object.keys(data).forEach(key => {
        const input = form.querySelector(`[name="${key}"]`);
        if (input) {
            if (input.type === 'checkbox') {
                input.checked = data[key] === 'on';
            } else {
                input.value = data[key];
            }
        }
    });
}

function setupProgressTracking() {
    // Track user progress through the application
    const milestones = [
        'data_uploaded',
        'first_analysis',
        'first_visualization',
        'first_statistical_test',
        'first_ml_model',
        'first_report'
    ];
    
    function trackMilestone(milestone) {
        const progress = JSON.parse(localStorage.getItem('user-progress') || '{}');
        if (!progress[milestone]) {
            progress[milestone] = new Date().toISOString();
            localStorage.setItem('user-progress', JSON.stringify(progress));
            
            // Show congratulations message
            showMilestoneAchievement(milestone);
        }
    }
    
    // Expose tracking function globally
    window.trackMilestone = trackMilestone;
}

function showMilestoneAchievement(milestone) {
    const messages = {
        'data_uploaded': 'Congratulations! You\'ve uploaded your first dataset!',
        'first_analysis': 'Great! You\'ve completed your first analysis!',
        'first_visualization': 'Awesome! You\'ve created your first visualization!',
        'first_statistical_test': 'Excellent! You\'ve run your first statistical test!',
        'first_ml_model': 'Outstanding! You\'ve trained your first ML model!',
        'first_report': 'Perfect! You\'ve generated your first report!'
    };
    
    showAlert('success', messages[milestone], 5000);
}

// Utility Functions

function showLoading(message = 'Loading...') {
    const overlay = document.getElementById('loading-overlay');
    const text = document.getElementById('loading-text');
    
    if (overlay && text) {
        text.textContent = message;
        overlay.classList.remove('d-none');
        
        // Auto-hide after 30 seconds
        clearTimeout(loadingTimeout);
        loadingTimeout = setTimeout(() => {
            hideLoading();
        }, 30000);
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('d-none');
    }
    clearTimeout(loadingTimeout);
}

function showAlert(type, message, duration = 3000) {
    const alertContainer = createAlertContainer();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    
    const icon = getAlertIcon(type);
    
    alertDiv.innerHTML = `
        <i class="fas ${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alertDiv);
    
    // Auto-dismiss
    if (duration > 0) {
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.classList.remove('show');
                setTimeout(() => {
                    if (alertDiv.parentNode) {
                        alertDiv.parentNode.removeChild(alertDiv);
                    }
                }, 150);
            }
        }, duration);
    }
    
    // Add animation
    alertDiv.classList.add('fade-in');
}

function createAlertContainer() {
    let container = document.getElementById('alert-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'alert-container';
        container.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 1050;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }
    return container;
}

function getAlertIcon(type) {
    const icons = {
        'success': 'fa-check-circle',
        'danger': 'fa-exclamation-triangle',
        'warning': 'fa-exclamation-circle',
        'info': 'fa-info-circle',
        'primary': 'fa-info-circle'
    };
    return icons[type] || 'fa-info-circle';
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined) return 'N/A';
    
    if (typeof num !== 'number') {
        num = parseFloat(num);
        if (isNaN(num)) return 'N/A';
    }
    
    return num.toLocaleString(undefined, {
        minimumFractionDigits: 0,
        maximumFractionDigits: decimals
    });
}

function formatPercentage(value, decimals = 1) {
    if (value === null || value === undefined) return 'N/A';
    
    if (typeof value !== 'number') {
        value = parseFloat(value);
        if (isNaN(value)) return 'N/A';
    }
    
    return (value * 100).toFixed(decimals) + '%';
}

function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('success', 'Copied to clipboard!');
        }).catch(err => {
            console.error('Failed to copy: ', err);
            fallbackCopyTextToClipboard(text);
        });
    } else {
        fallbackCopyTextToClipboard(text);
    }
}

function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.position = 'fixed';
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showAlert('success', 'Copied to clipboard!');
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
        showAlert('danger', 'Failed to copy to clipboard');
    }
    
    document.body.removeChild(textArea);
}

function exportData(data, filename, type = 'json') {
    let content, mimeType;
    
    switch (type) {
        case 'json':
            content = JSON.stringify(data, null, 2);
            mimeType = 'application/json';
            break;
        case 'csv':
            content = convertToCSV(data);
            mimeType = 'text/csv';
            break;
        case 'txt':
            content = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
            mimeType = 'text/plain';
            break;
        default:
            content = JSON.stringify(data, null, 2);
            mimeType = 'application/json';
    }
    
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

function convertToCSV(data) {
    if (!Array.isArray(data) || data.length === 0) {
        return '';
    }
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => {
            const value = row[header];
            return typeof value === 'string' && value.includes(',') ? `"${value}"` : value;
        }).join(','))
    ].join('\n');
    
    return csvContent;
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validateURL(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

function sanitizeHTML(str) {
    const temp = document.createElement('div');
    temp.textContent = str;
    return temp.innerHTML;
}

function createToast(title, message, type = 'info') {
    const toastContainer = getToastContainer();
    
    const toastDiv = document.createElement('div');
    toastDiv.className = 'toast';
    toastDiv.setAttribute('role', 'alert');
    toastDiv.innerHTML = `
        <div class="toast-header">
            <i class="fas ${getAlertIcon(type)} me-2 text-${type}"></i>
            <strong class="me-auto">${sanitizeHTML(title)}</strong>
            <small>now</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${sanitizeHTML(message)}
        </div>
    `;
    
    toastContainer.appendChild(toastDiv);
    
    const toast = new bootstrap.Toast(toastDiv);
    toast.show();
    
    toastDiv.addEventListener('hidden.bs.toast', () => {
        toastDiv.remove();
    });
}

function getToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
    }
    return container;
}

function initializeNotifications() {
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

function showNotification(title, options = {}) {
    if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification(title, {
            icon: '/static/favicon.ico',
            badge: '/static/favicon.ico',
            ...options
        });
        
        notification.onclick = function() {
            window.focus();
            notification.close();
        };
        
        setTimeout(() => {
            notification.close();
        }, 5000);
    }
}

function checkForUpdates() {
    // Check for application updates
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready.then(registration => {
            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        showAlert('info', 'A new version is available. Refresh to update.', 0);
                    }
                });
            });
        });
    }
}

// Navigation functions
function showColumnAnalysis() {
    if (getCurrentDatasetId()) {
        window.location.href = `/analysis/column/${getCurrentDatasetId()}`;
    } else {
        // Show dataset selector modal for column analysis
        showDatasetSelectorModal('column_analysis');
    }
}

function showStatisticalTests() {
    if (getCurrentDatasetId()) {
        window.location.href = `/statistics/${getCurrentDatasetId()}`;
    } else {
        // Show dataset selector modal for statistical tests
        showDatasetSelectorModal('statistics');
    }
}

function showMLModels() {
    if (getCurrentDatasetId()) {
        window.location.href = `/ml/${getCurrentDatasetId()}`;
    } else {
        // Show dataset selector modal for ML models
        showDatasetSelectorModal('ml_models');
    }
}

function showVisualization() {
    if (getCurrentDatasetId()) {
        window.location.href = `/visualization/${getCurrentDatasetId()}`;
    } else {
        // Show dataset selector modal for visualizations
        showDatasetSelectorModal('visualization');
    }
}

function showFeatureEngineering() {
    if (getCurrentDatasetId()) {
        window.location.href = `/feature-engineering/${getCurrentDatasetId()}`;
    } else {
        // Show dataset selector modal for feature engineering
        showDatasetSelectorModal('feature_engineering');
    }
}

function showDatasetSelectorModal(targetPage) {
    // Create and show dataset selector modal
    const modalHtml = `
        <div class="modal fade" id="datasetSelectorModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content bg-dark">
                    <div class="modal-header border-secondary">
                        <h5 class="modal-title">
                            <i class="fas fa-database me-2"></i>Select Dataset
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div id="dataset-list-container">
                            <div class="text-center">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="mt-2">Loading datasets...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if present
    const existingModal = document.getElementById('datasetSelectorModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('datasetSelectorModal'));
    modal.show();
    
    // Load datasets
    loadDatasetsForSelector(targetPage);
}

function loadDatasetsForSelector(targetPage) {
    // Simulate API call to get datasets
    setTimeout(() => {
        const datasets = [
            { id: 1, filename: "sales_data_2023.csv", rows: 1500, cols: 12 },
            { id: 2, filename: "customer_analysis.xlsx", rows: 2300, cols: 15 },
            { id: 3, filename: "marketing_data.json", rows: 890, cols: 8 }
        ];
        
        const container = document.getElementById('dataset-list-container');
        
        if (datasets.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-database fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">No datasets found</h5>
                    <p class="text-muted">Please upload a dataset first.</p>
                    <a href="/upload" class="btn btn-primary">
                        <i class="fas fa-upload me-2"></i>Upload Dataset
                    </a>
                </div>
            `;
            return;
        }
        
        let html = `
            <div class="row">
                <div class="col-12 mb-3">
                    <h6 class="text-muted">Select a dataset for ${targetPage.replace('_', ' ')}:</h6>
                </div>
        `;
        
        datasets.forEach(dataset => {
            html += `
                <div class="col-md-6 mb-3">
                    <div class="card bg-secondary h-100 dataset-card" 
                         onclick="selectDataset(${dataset.id}, '${targetPage}')" 
                         style="cursor: pointer;">
                        <div class="card-body">
                            <h6 class="card-title">
                                <i class="fas fa-file-csv me-2 text-primary"></i>
                                ${dataset.filename}
                            </h6>
                            <p class="card-text text-muted small">
                                ${dataset.rows} rows × ${dataset.cols} columns
                            </p>
                            <div class="text-end">
                                <span class="badge bg-primary">Select</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
        
        // Add hover effects
        const datasetCards = document.querySelectorAll('.dataset-card');
        datasetCards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.02)';
                this.style.transition = 'transform 0.2s ease';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
            });
        });
        
    }, 1000);
}

function selectDataset(datasetId, targetPage) {
    // Set current dataset
    setCurrentDatasetId(datasetId);
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('datasetSelectorModal'));
    if (modal) {
        modal.hide();
    }
    
    // Navigate to target page
    const pageUrls = {
        'column_analysis': `/analysis/column/${datasetId}`,
        'statistics': `/statistics/${datasetId}`,
        'ml_models': `/ml/${datasetId}`,
        'visualization': `/visualization/${datasetId}`,
        'feature_engineering': `/feature-engineering/${datasetId}`
    };
    
    const url = pageUrls[targetPage];
    if (url) {
        showLoading(`Loading ${targetPage.replace('_', ' ')}...`);
        window.location.href = url;
    } else {
        showAlert('error', 'Invalid page selected');
    }
}

// Enhanced dataset management functions
function getCurrentDatasetId() {
    // Check if dataset ID is in URL
    const pathParts = window.location.pathname.split('/');
    const datasetIndex = pathParts.findIndex(part => part === 'dataset' || part === 'analysis' || part === 'statistics' || part === 'ml' || part === 'visualization' || part === 'feature-engineering');
    
    if (datasetIndex !== -1 && pathParts[datasetIndex + 1]) {
        const id = parseInt(pathParts[datasetIndex + 1]);
        if (!isNaN(id)) {
            currentDatasetId = id;
            return id;
        }
    }
    
    // Check localStorage
    const storedId = localStorage.getItem('currentDatasetId');
    if (storedId) {
        currentDatasetId = parseInt(storedId);
        return currentDatasetId;
    }
    
    // Check session storage
    const sessionId = sessionStorage.getItem('currentDatasetId');
    if (sessionId) {
        currentDatasetId = parseInt(sessionId);
        return currentDatasetId;
    }
    
    return null;
}

function setCurrentDatasetId(datasetId) {
    currentDatasetId = datasetId;
    localStorage.setItem('currentDatasetId', datasetId.toString());
    sessionStorage.setItem('currentDatasetId', datasetId.toString());
    
    // Update UI elements that show current dataset
    updateCurrentDatasetDisplay();
}

function updateCurrentDatasetDisplay() {
    // Update any UI elements that show the current dataset
    const datasetDisplays = document.querySelectorAll('.current-dataset-display');
    datasetDisplays.forEach(display => {
        if (currentDatasetId) {
            display.textContent = `Dataset ID: ${currentDatasetId}`;
            display.classList.remove('d-none');
        } else {
            display.classList.add('d-none');
        }
    });
}

// Enhanced navigation functions
function navigateToPage(page, datasetId = null) {
    const id = datasetId || getCurrentDatasetId();
    
    const routes = {
        'dashboard': '/',
        'upload': '/upload',
        'analysis': id ? `/analysis/dataset/${id}` : '/analysis',
        'column_analysis': id ? `/analysis/column/${id}` : '/analysis',
        'comparison': '/analysis/comparison',
        'statistics': id ? `/statistics/${id}` : '/statistics',
        'visualization': id ? `/visualization/${id}` : '/visualization',
        'ml_models': id ? `/ml/${id}` : '/ml',
        'feature_engineering': id ? `/feature-engineering/${id}` : '/feature-engineering',
        'advanced_feature_engineering': '/feature-engineering/advanced',
        'reports': '/reports'
    };
    
    const url = routes[page];
    if (url) {
        if (url.includes('undefined') || (!id && page !== 'dashboard' && page !== 'upload' && page !== 'comparison' && page !== 'advanced_feature_engineering' && page !== 'reports')) {
            showDatasetSelectorModal(page);
        } else {
            window.location.href = url;
        }
    } else {
        showAlert('error', `Unknown page: ${page}`);
    }
}

// Enhanced error handling
function handleNavigationError(error) {
    console.error('Navigation error:', error);
    showAlert('error', 'Navigation failed. Please try again.');
}

// Enhanced page initialization
function initializePage() {
    // Detect current page and initialize accordingly
    const path = window.location.pathname;
    
    if (path.includes('/analysis/')) {
        initializeAnalysisPage();
    } else if (path.includes('/visualization/')) {
        initializeVisualizationPage();
    } else if (path.includes('/statistics/')) {
        initializeStatisticsPage();
    } else if (path.includes('/ml/')) {
        initializeMLPage();
    } else if (path.includes('/feature-engineering/')) {
        initializeFeatureEngineeringPage();
    } else if (path === '/' || path === '/dashboard') {
        initializeDashboardPage();
    }
    
    // Update current dataset display
    updateCurrentDatasetDisplay();
}

function initializeAnalysisPage() {
    console.log('Initializing analysis page');
    // Add analysis-specific initialization
}

function initializeVisualizationPage() {
    console.log('Initializing visualization page');
    // Add visualization-specific initialization
}

function initializeStatisticsPage() {
    console.log('Initializing statistics page');
    // Add statistics-specific initialization
}

function initializeMLPage() {
    console.log('Initializing ML page');
    // Add ML-specific initialization
}

function initializeFeatureEngineeringPage() {
    console.log('Initializing feature engineering page');
    // Add feature engineering-specific initialization
}

function initializeDashboardPage() {
    console.log('Initializing dashboard page');
    // Add dashboard-specific initialization
}

// Enhanced connectivity check
function checkConnectivity() {
    // Check if all required resources are loaded
    const requiredResources = [
        'bootstrap',
        'Chart',
        'Plotly'
    ];
    
    const missingResources = requiredResources.filter(resource => {
        return typeof window[resource] === 'undefined';
    });
    
    if (missingResources.length > 0) {
        console.warn('Missing resources:', missingResources);
        showAlert('warning', `Some features may not work properly. Missing: ${missingResources.join(', ')}`);
    }
    
    // Check backend connectivity
    fetch('/api/health-check', { method: 'HEAD' })
        .then(response => {
            if (response.ok) {
                console.log('Backend connectivity: OK');
            } else {
                throw new Error('Backend not responding');
            }
        })
        .catch(error => {
            console.warn('Backend connectivity issue:', error);
            showAlert('warning', 'Some features may be limited due to connectivity issues.');
        });
}

// Add page-specific enhancements
function enhanceCurrentPage() {
    // Add interactive elements
    const interactiveElements = document.querySelectorAll('.interactive-hover');
    interactiveElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
            this.style.transition = 'transform 0.3s ease';
        });
        
        element.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    // Add pulse animation to important buttons
    const pulseButtons = document.querySelectorAll('.pulse-on-hover');
    pulseButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.classList.add('pulse');
        });
        
        button.addEventListener('mouseleave', function() {
            this.classList.remove('pulse');
        });
    });
}

// Call enhancement function after page load
window.addEventListener('load', enhanceCurrentPage);

// Enhanced dataset loading with proper ID management
function loadDatasetForAnalysis(datasetId) {
    if (!datasetId) {
        showAlert('error', 'No dataset ID provided');
        return;
    }
    
    setCurrentDatasetId(datasetId);
    
    // Load basic dataset information
    fetch(`/analysis/api/column_details/${datasetId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayDatasetInfo(data);
                showAlert('success', 'Dataset loaded successfully');
            } else {
                showAlert('error', data.error || 'Failed to load dataset information');
            }
        })
        .catch(error => {
            console.error('Error loading dataset:', error);
            showAlert('error', 'Network error loading dataset');
        });
}

function displayDatasetInfo(data) {
    // Update dataset information display
    const infoContainer = document.getElementById('dataset-info-container');
    if (infoContainer && data.column_details) {
        const columns = Object.keys(data.column_details);
        const numericColumns = columns.filter(col => 
            ['int64', 'float64'].includes(data.column_details[col].data_type)
        );
        const categoricalColumns = columns.filter(col => 
            ['object', 'category'].includes(data.column_details[col].data_type)
        );
        
        infoContainer.innerHTML = `
            <div class="card bg-dark border-info">
                <div class="card-body">
                    <h6><i class="fas fa-database me-2"></i>Dataset Overview</h6>
                    <div class="row">
                        <div class="col-md-3">
                            <small class="text-muted">Shape:</small><br>
                            <strong>${data.dataset_shape[0]} rows × ${data.dataset_shape[1]} columns</strong>
                        </div>
                        <div class="col-md-3">
                            <small class="text-muted">Numeric Columns:</small><br>
                            <strong>${numericColumns.length}</strong>
                        </div>
                        <div class="col-md-3">
                            <small class="text-muted">Categorical Columns:</small><br>
                            <strong>${categoricalColumns.length}</strong>
                        </div>
                        <div class="col-md-3">
                            <small class="text-muted">Memory Usage:</small><br>
                            <strong>${data.total_memory_usage.toFixed(2)} MB</strong>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Update column details table
    const tableContainer = document.getElementById('column-details-table');
    if (tableContainer && data.column_details) {
        let tableHTML = `
            <div class="table-responsive">
                <table class="table table-dark table-striped table-hover">
                    <thead class="table-secondary">
                        <tr>
                            <th>Column</th>
                            <th>Type</th>
                            <th>Non-Null</th>
                            <th>Missing</th>
                            <th>Unique</th>
                            <th>Min</th>
                            <th>Max</th>
                            <th>Mean</th>
                            <th>Std</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        Object.keys(data.column_details).forEach(col => {
            const details = data.column_details[col];
            tableHTML += `
                <tr>
                    <td><strong>${col}</strong></td>
                    <td><span class="badge bg-primary">${details.data_type}</span></td>
                    <td>${details.non_null_count}</td>
                    <td>${details.null_count} (${details.null_percentage.toFixed(1)}%)</td>
                    <td>${details.unique_count}</td>
                    <td>${details.min !== undefined ? details.min.toFixed(2) : 'N/A'}</td>
                    <td>${details.max !== undefined ? details.max.toFixed(2) : 'N/A'}</td>
                    <td>${details.mean !== undefined ? details.mean.toFixed(2) : 'N/A'}</td>
                    <td>${details.std !== undefined ? details.std.toFixed(2) : 'N/A'}</td>
                </tr>
            `;
        });
        
        tableHTML += `
                    </tbody>
                </table>
            </div>
        `;
        
        tableContainer.innerHTML = tableHTML;
    }
}

// Error handling
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
    showAlert('danger', 'An unexpected error occurred. Please refresh the page and try again.');
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showAlert('warning', 'A background operation failed. Some features may not work correctly.');
});

// Expose global functions
window.EDAProUtils = {
    showLoading,
    hideLoading,
    showAlert,
    formatFileSize,
    formatNumber,
    formatPercentage,
    copyToClipboard,
    exportData,
    createToast,
    showNotification,
    validateEmail,
    validateURL,
    sanitizeHTML,
    debounce,
    throttle
};

console.log('EDA Pro main.js loaded successfully');
