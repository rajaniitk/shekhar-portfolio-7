 // Common JavaScript utilities for EDA Pro application
 
 // Loading overlay functionality
 let loadingOverlay = null;
 
 function showLoading(message = 'Loading...') {
     // Remove existing loading overlay if present
     hideLoading();
     
     // Create loading overlay
     loadingOverlay = document.createElement('div');
     loadingOverlay.id = 'loading-overlay';
     loadingOverlay.innerHTML = `
         <div class="loading-content">
             <div class="spinner-border text-primary" role="status">
                 <span class="visually-hidden">Loading...</span>
             </div>
             <div class="loading-text mt-3">${message}</div>
         </div>
     `;
     
     // Add styles
     loadingOverlay.style.cssText = `
         position: fixed;
         top: 0;
         left: 0;
         width: 100%;
         height: 100%;
         background: rgba(0, 0, 0, 0.8);
         display: flex;
         justify-content: center;
         align-items: center;
         z-index: 9999;
         color: white;
         text-align: center;
     `;
     
     // Add to document
     document.body.appendChild(loadingOverlay);
 }
 
 function hideLoading() {
     if (loadingOverlay) {
         loadingOverlay.remove();
         loadingOverlay = null;
     }
 }
 
 // Alert functionality
 function showAlert(type, message, duration = 5000) {
     // Remove existing alerts
     const existingAlerts = document.querySelectorAll('.custom-alert');
     existingAlerts.forEach(alert => alert.remove());
     
     // Create alert element
     const alert = document.createElement('div');
     alert.className = `alert alert-${type} alert-dismissible custom-alert`;
     alert.style.cssText = `
         position: fixed;
         top: 20px;
         right: 20px;
         z-index: 10000;
         min-width: 300px;
         max-width: 500px;
     `;
     
     // Get appropriate icon
     const iconMap = {
         'success': 'fa-check-circle',
         'danger': 'fa-exclamation-triangle',
         'warning': 'fa-exclamation-circle',
         'info': 'fa-info-circle'
     };
     const icon = iconMap[type] || 'fa-info-circle';
     
     alert.innerHTML = `
         <i class="fas ${icon} me-2"></i>
         ${message}
         <button type="button" class="btn-close" aria-label="Close"></button>
     `;
     
     // Add to document
     document.body.appendChild(alert);
     
     // Add close functionality
     const closeBtn = alert.querySelector('.btn-close');
     closeBtn.addEventListener('click', () => alert.remove());
     
     // Auto-remove after duration
     if (duration > 0) {
         setTimeout(() => {
             if (alert.parentNode) {
                 alert.remove();
             }
         }, duration);
     }
 }
 
 // Utility functions for data formatting
 function formatNumber(num, decimals = 2) {
     if (num === null || num === undefined || isNaN(num)) {
         return 'N/A';
     }
     return Number(num).toFixed(decimals);
 }
 
 function formatPercentage(num, decimals = 1) {
     if (num === null || num === undefined || isNaN(num)) {
         return 'N/A';
     }
     return Number(num).toFixed(decimals) + '%';
 }
 
 function formatLargeNumber(num) {
     if (num === null || num === undefined || isNaN(num)) {
         return 'N/A';
     }
     
     if (num >= 1000000000) {
         return (num / 1000000000).toFixed(1) + 'B';
     } else if (num >= 1000000) {
         return (num / 1000000).toFixed(1) + 'M';
     } else if (num >= 1000) {
         return (num / 1000).toFixed(1) + 'K';
     }
     return num.toString();
 }
 
 // Utility for safe JSON parsing
 function safeJsonParse(jsonString, defaultValue = null) {
     try {
         return JSON.parse(jsonString);
     } catch (e) {
         console.error('Error parsing JSON:', e);
         return defaultValue;
     }
 }
 
 // Utility for debouncing function calls
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
 
 // Utility for throttling function calls
 function throttle(func, limit) {
     let inThrottle;
     return function(...args) {
         if (!inThrottle) {
             func.apply(this, args);
             inThrottle = true;
             setTimeout(() => inThrottle = false, limit);
         }
     };
 }
 
 // File download utility
 function downloadBlob(blob, filename) {
     const url = URL.createObjectURL(blob);
     const a = document.createElement('a');
     a.href = url;
     a.download = filename;
     document.body.appendChild(a);
     a.click();
     document.body.removeChild(a);
     URL.revokeObjectURL(url);
 }
 
 // Copy text to clipboard utility
 async function copyToClipboard(text) {
     try {
         await navigator.clipboard.writeText(text);
         showAlert('success', 'Copied to clipboard!', 2000);
     } catch (err) {
         // Fallback for older browsers
         const textArea = document.createElement('textarea');
         textArea.value = text;
         document.body.appendChild(textArea);
         textArea.select();
         try {
             document.execCommand('copy');
             showAlert('success', 'Copied to clipboard!', 2000);
         } catch (fallbackErr) {
             showAlert('danger', 'Failed to copy to clipboard');
         }
         document.body.removeChild(textArea);
     }
 }
 
 // Validate dataset ID
 function validateDatasetId(datasetId) {
     if (!datasetId || datasetId === 'null' || datasetId === null) {
         showAlert('warning', 'No dataset selected. Please upload a dataset first.');
         return false;
     }
     return true;
 }
 
 // Handle API response errors
 function handleApiError(response, defaultMessage = 'An error occurred') {
     if (!response.ok) {
         throw new Error(`HTTP ${response.status}: ${response.statusText}`);
     }
     return response;
 }
 
 // Make API request with error handling
 async function makeApiRequest(url, options = {}) {
     try {
         const response = await fetch(url, {
             headers: {
                 'Content-Type': 'application/json',
                 ...options.headers
             },
             ...options
         });
         
         handleApiError(response);
         return await response.json();
     } catch (error) {
         console.error('API request failed:', error);
         throw error;
     }
 }
 
 // Initialize common functionality when DOM is loaded
 document.addEventListener('DOMContentLoaded', function() {
     // Add Bootstrap tooltips to elements with data-bs-toggle="tooltip"
     const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
     const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
         return new bootstrap.Tooltip(tooltipTriggerEl);
     });
     
     // Add loading state to buttons when clicked
     const buttons = document.querySelectorAll('button[onclick]');
     buttons.forEach(button => {
         const originalOnClick = button.onclick;
         button.addEventListener('click', function(e) {
             // Add loading state
             const originalText = this.innerHTML;
             const wasDisabled = this.disabled;
             
             this.disabled = true;
             this.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Loading...';
             
             // Execute original onclick
             try {
                 originalOnClick.call(this, e);
             } catch (error) {
                 console.error('Button click error:', error);
                 showAlert('danger', 'An error occurred while processing your request.');
             } finally {
                 // Restore button state after a short delay
                 setTimeout(() => {
                     this.disabled = wasDisabled;
                     this.innerHTML = originalText;
                 }, 1000);
             }
         });
     });
     
     // Auto-hide alerts after some time
     const alerts = document.querySelectorAll('.alert:not(.custom-alert)');
     alerts.forEach(alert => {
         setTimeout(() => {
             if (alert.parentNode) {
                 alert.style.transition = 'opacity 0.5s';
                 alert.style.opacity = '0';
                 setTimeout(() => alert.remove(), 500);
             }
         }, 5000);
     });
 });
 
 // Export functions for use in other scripts
 window.EDAUtils = {
     showLoading,
     hideLoading,
     showAlert,
     formatNumber,
     formatPercentage,
     formatLargeNumber,
     safeJsonParse,
     debounce,
     throttle,
     downloadBlob,
     copyToClipboard,
     validateDatasetId,
     handleApiError,
     makeApiRequest
 };