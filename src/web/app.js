/**
 * ANP Ports Vessel Scraper Dashboard
 * Frontend JavaScript for vessel monitoring interface
 */

// Global variables
let currentData = null;
let currentFilters = {};
let vesselTypesChart = null;
let operatorsChart = null;

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚢 ANP Ports Vessel Scraper Dashboard initialized');
    
    // Check if Tabler Icons are loaded and provide fallbacks
    checkIconSupport();
    
    // Load initial data
    loadDashboardData();
    
    // Set up filter event listeners
    setupFilterListeners();
    
    // Test API connection
    testConnection();
});

// Check if Tabler Icons are loaded and provide fallbacks
function checkIconSupport() {
    // Test if Tabler Icons are working
    const testIcon = document.createElement('i');
    testIcon.className = 'ti ti-ship';
    testIcon.style.display = 'none';
    document.body.appendChild(testIcon);
    
    // Check if the icon has content (indicating it's loaded)
    const iconLoaded = testIcon.offsetWidth > 0 || testIcon.offsetHeight > 0;
    document.body.removeChild(testIcon);
    
    if (!iconLoaded) {
        console.warn('Tabler Icons not loaded, using fallback icons');
        replaceTablerIcons();
    }
}

// Replace Tabler Icons with fallback icons
function replaceTablerIcons() {
    // Replace ship icons
    document.querySelectorAll('.ti.ti-ship').forEach(icon => {
        icon.className = 'icon-fallback icon-ship';
    });
    
    // Replace refresh icons
    document.querySelectorAll('.ti.ti-refresh').forEach(icon => {
        icon.className = 'icon-fallback icon-refresh';
    });
    
    // Replace download icons
    document.querySelectorAll('.ti.ti-download').forEach(icon => {
        icon.className = 'icon-fallback icon-download';
    });
    
    // Replace trash icons
    document.querySelectorAll('.ti.ti-trash').forEach(icon => {
        icon.className = 'icon-fallback icon-trash';
    });
    
    // Also replace icons with data-icon-type attributes
    document.querySelectorAll('[data-icon-type="ship"]').forEach(icon => {
        if (icon.classList.contains('ti')) {
            icon.className = 'icon-fallback icon-ship';
        }
    });
}

// Setup filter event listeners
function setupFilterListeners() {
    // Search filter with debouncing
    let searchTimeout;
    document.getElementById('search-filter').addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            applyFilters();
        }, 500);
    });
    
    // Date filters
    document.getElementById('start-date').addEventListener('change', applyFilters);
    document.getElementById('end-date').addEventListener('update', applyFilters);
    
    // Dropdown filters
    document.getElementById('vessel-type-filter').addEventListener('change', applyFilters);
    document.getElementById('operator-filter').addEventListener('change', applyFilters);
    document.getElementById('port-filter').addEventListener('change', applyFilters);
}

// Load dashboard data
async function loadDashboardData() {
    try {
        showLoading(true);
        
        const response = await fetch('/api/dashboard-data');
        const data = await response.json();
        
        if (data.status === 'success') {
            currentData = data;
            updateDashboard(data);
            updateCharts(data.statistics);
            populateFilterOptions(data.statistics);
        } else {
            showError('Failed to load dashboard data');
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('Failed to load dashboard data: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Update dashboard with new data
function updateDashboard(data) {
    const stats = data.statistics;
    
    // Update KPI cards
    document.getElementById('total-vessels').textContent = stats.total_vessels || 0;
    document.getElementById('last-update').textContent = formatDate(stats.last_update) || 'Never';
    
    // Calculate active vessels (vessels with recent activity)
    const activeVessels = data.vessels.filter(v => {
        if (!v.parsed_date) return false;
        const vesselDate = new Date(v.parsed_date);
        const now = new Date();
        const daysDiff = (now - vesselDate) / (1000 * 60 * 60 * 24);
        return daysDiff <= 7; // Active if within 7 days
    }).length;
    
    document.getElementById('active-vessels').textContent = activeVessels;
    
    // Count vessels in port
    const inPortCount = data.vessels.filter(v => 
        v.sITUATIONField === 'A QUAI' || v.sITUATIONField === 'EN RADE'
    ).length;
    document.getElementById('in-port-count').textContent = inPortCount;
    
    // Vessel types count
    const vesselTypesCount = Object.keys(stats.vessel_types || {}).length;
    document.getElementById('vessel-types-count').textContent = vesselTypesCount;
    
    // Most common vessel type
    const mostCommonType = Object.entries(stats.vessel_types || {})[0];
    if (mostCommonType) {
        document.getElementById('most-common-type').textContent = mostCommonType[0];
    }
    
    // System status
    document.getElementById('system-status').textContent = 'Active';
    document.getElementById('api-status').textContent = 'Connected';
    
    // Update results count
    document.getElementById('results-count').textContent = `${data.total_results} results`;
    
    // Update vessels table
    updateVesselsTable(data.vessels);
}

// Update vessels table
function updateVesselsTable(vessels) {
    const tbody = document.getElementById('vessels-tbody');
    
    if (!vessels || vessels.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted">
                    <i class="ti ti-ship me-2"></i>Aucun navire trouvé
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = vessels.map(vessel => `
        <tr>
            <td>
                <div class="d-flex align-items-center">
                
                    <div>
                        <div class="font-weight-medium">${vessel.nOM_NAVIREField || 'Inconnu'}</div>
                        <div class="text-muted">IMO: ${vessel.nUMERO_LLOYDField || 'N/A'}</div>
                    </div>
                </div>
            </td>
            <td>
                ${formatVesselTypeBadges(vessel.tYP_NAVIREField)}
            </td>
            <td>
                <span class="badge situation-badge">
                    ${vessel.sITUATIONField || 'Inconnu'}
                </span>
            </td>
            <td>
                ${formatDateOnly(vessel.parsed_date) || 'Inconnu'}
            </td>
            <td>
                ${formatTimeOnly(vessel.parsed_date) || 'Inconnu'}
            </td>
            <td>
                ${formatPortBadges(vessel.pROVField)}
            </td>
            <td>
                ${vessel.cONSIGNATAIREField || 'Inconnu'}
            </td>
            <td>
                ${formatOperatorBadges(vessel.oPERATEURField)}
            </td>
        </tr>
    `).join('');
}

// Update charts
function updateCharts(stats) {
    // Vessel types chart
    if (vesselTypesChart) {
        vesselTypesChart.destroy();
    }
    
    const vesselTypesCtx = document.getElementById('vessel-types-chart').getContext('2d');
    const vesselTypesData = Object.entries(stats.vessel_types || {}).slice(0, 8);
    
    vesselTypesChart = new Chart(vesselTypesCtx, {
        type: 'doughnut',
        data: {
            labels: vesselTypesData.map(([type, _]) => type),
            datasets: [{
                data: vesselTypesData.map(([_, count]) => count),
                backgroundColor: [
                    '#206bc4', '#d63939', '#2fb344', '#f59f00',
                    '#ae3ec9', '#0ca678', '#f76707', '#5c7cfa'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
    
    // Operators chart
    if (operatorsChart) {
        operatorsChart.destroy();
    }
    
    const operatorsCtx = document.getElementById('operators-chart').getContext('2d');
    const operatorsData = Object.entries(stats.operators || {}).slice(0, 8);
    
    operatorsChart = new Chart(operatorsCtx, {
        type: 'bar',
        data: {
            labels: operatorsData.map(([operator, _]) => operator),
            datasets: [{
                label: 'Vessels',
                data: operatorsData.map(([_, count]) => count),
                backgroundColor: '#206bc4'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Populate filter options
function populateFilterOptions(stats) {
    // Vessel types
    const vesselTypeSelect = document.getElementById('vessel-type-filter');
    vesselTypeSelect.innerHTML = '<option value="">All Types</option>';
    Object.keys(stats.vessel_types || {}).forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type;
        vesselTypeSelect.appendChild(option);
    });
    
    // Operators
    const operatorSelect = document.getElementById('operator-filter');
    operatorSelect.innerHTML = '<option value="">All Operators</option>';
    Object.keys(stats.operators || {}).forEach(operator => {
        const option = document.createElement('option');
        option.value = operator;
        option.textContent = operator;
        operatorSelect.appendChild(option);
    });
    
    // Ports
    const portSelect = document.getElementById('port-filter');
    portSelect.innerHTML = '<option value="">All Ports</option>';
    Object.keys(stats.ports || {}).forEach(port => {
        const option = document.createElement('option');
        option.value = port;
        option.textContent = port;
        portSelect.appendChild(option);
    });
}

// Apply filters
async function applyFilters() {
    try {
        showLoading(true);
        
        // Build filter parameters
        const params = new URLSearchParams();
        
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        const vesselType = document.getElementById('vessel-type-filter').value;
        const operator = document.getElementById('operator-filter').value;
        const port = document.getElementById('port-filter').value;
        const search = document.getElementById('search-filter').value;
        
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        if (vesselType) params.append('vessel_type', vesselType);
        if (operator) params.append('operator', operator);
        if (port) params.append('port', port);
        if (search) params.append('search', search);
        
        // Store current filters
        currentFilters = Object.fromEntries(params);
        
        // Fetch filtered data
        const response = await fetch(`/api/dashboard-data?${params.toString()}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            currentData = data;
            updateDashboard(data);
            updateCharts(data.statistics);
        } else {
            showError('Failed to apply filters');
        }
    } catch (error) {
        console.error('Error applying filters:', error);
        showError('Failed to apply filters: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Clear filters
function clearFilters() {
    document.getElementById('start-date').value = '';
    document.getElementById('end-date').value = '';
    document.getElementById('vessel-type-filter').value = '';
    document.getElementById('operator-filter').value = '';
    document.getElementById('port-filter').value = '';
    document.getElementById('search-filter').value = '';
    
    currentFilters = {};
    loadDashboardData();
}

// Update data from API
async function updateData() {
    try {
        showLoading(true);
        
        const response = await fetch('/api/update?force_update=true', {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.status === 'success') {
            showSuccess(`Update successful! ${result.new_vessels} new vessels added.`);
            loadDashboardData(); // Reload data
        } else {
            showError(`Update failed: ${result.message}`);
        }
    } catch (error) {
        console.error('Error updating data:', error);
        showError('Failed to update data: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Export CSV
async function exportCSV() {
    try {
        // Build filter parameters
        const params = new URLSearchParams();
        Object.entries(currentFilters).forEach(([key, value]) => {
            if (value) params.append(key, value);
        });
        
        const response = await fetch(`/api/export/csv?${params.toString()}`);
        const data = await response.json();
        
        if (data.csv_data) {
            // Create and download CSV file
            const blob = new Blob([data.csv_data], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `anp-vessels-${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showSuccess('CSV exported successfully!');
        } else {
            showError('No data to export');
        }
    } catch (error) {
        console.error('Error exporting CSV:', error);
        showError('Failed to export CSV: ' + error.message);
    }
}

// Clean duplicates
async function cleanDuplicates() {
    if (!confirm('Are you sure you want to clean duplicate vessels? This action cannot be undone.')) {
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch('/api/clean-duplicates', {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.status === 'success') {
            showSuccess(`Cleanup successful! ${result.duplicates_removed} duplicates removed.`);
            loadDashboardData(); // Reload data
        } else {
            showError(`Cleanup failed: ${result.message}`);
        }
    } catch (error) {
        console.error('Error cleaning duplicates:', error);
        showError('Failed to clean duplicates: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Test connection
async function testConnection() {
    try {
        const response = await fetch('/api/test-connection');
        const result = await response.json();
        
        if (result.status === 'success') {
            document.getElementById('api-status').textContent = 'Connected';
            document.getElementById('api-status').className = 'text-success';
        } else {
            document.getElementById('api-status').textContent = 'Disconnected';
            document.getElementById('api-status').className = 'text-danger';
        }
    } catch (error) {
        console.error('Error testing connection:', error);
        document.getElementById('api-status').textContent = 'Error';
        document.getElementById('api-status').className = 'text-danger';
    }
}

// View vessel details
function viewVesselDetails(escaleNumber) {
    if (!escaleNumber) return;
    
    // Find vessel in current data
    const vessel = currentData.vessels.find(v => v.nUMERO_ESCALEField == escaleNumber);
    if (!vessel) return;
    
    // Create modal with vessel details
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Vessel Details: ${vessel.nOM_NAVIREField}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Basic Information</h6>
                            <table class="table table-sm">
                                <tr><td>Name:</td><td>${vessel.nOM_NAVIREField || 'N/A'}</td></tr>
                                <tr><td>Type:</td><td>${vessel.tYP_NAVIREField || 'N/A'}</td></tr>
                                <tr><td>Operator:</td><td>${vessel.oPERATEURField || 'N/A'}</td></tr>
                                <tr><td>Escale #:</td><td>${vessel.nUMERO_ESCALEField || 'N/A'}</td></tr>
                                <tr><td>Lloyd #:</td><td>${vessel.nUMERO_LLOYDField || 'N/A'}</td></tr>
                            </table>
                        </div>
                        <div class="col-md-6">
                            <h6>Location & Status</h6>
                            <table class="table table-sm">
                                <tr><td>Port:</td><td>${vessel.pROVField || 'N/A'}</td></tr>
                                <tr><td>Situation:</td><td>${vessel.sITUATIONField || 'N/A'}</td></tr>
                                <tr><td>Consignee:</td><td>${vessel.cONSIGNATAIREField || 'N/A'}</td></tr>
                                <tr><td>Date:</td><td>${formatDate(vessel.parsed_date) || 'N/A'}</td></tr>
                                <tr><td>Scraped:</td><td>${formatDate(vessel.scraped_at) || 'N/A'}</td></tr>
                            </table>
                        </div>
                    </div>
                    ${vessel.filter_details ? `
                    <div class="mt-3">
                        <h6>Filter Details</h6>
                        <p><strong>Match Score:</strong> ${vessel.filter_details.match_score}</p>
                        <p><strong>Groups Matched:</strong> ${vessel.filter_details.groups_matched}/3</p>
                        <p><strong>Keywords Found:</strong></p>
                        <ul>
                            ${vessel.filter_details.vessel_type_keywords.map(k => `<li>Vessel Type: ${k}</li>`).join('')}
                            ${vessel.filter_details.operator_keywords.map(k => `<li>Operator: ${k}</li>`).join('')}
                            ${vessel.filter_details.port_location_keywords.map(k => `<li>Port: ${k}</li>`).join('')}
                        </ul>
                    </div>
                    ` : ''}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Clean up modal after hiding
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
}

// Copy vessel info
function copyVesselInfo(vesselName) {
    if (!vesselName) return;
    
    navigator.clipboard.writeText(vesselName).then(() => {
        showSuccess('Vessel name copied to clipboard!');
    }).catch(() => {
        showError('Failed to copy vessel name');
    });
}

// Utility functions
function formatDate(dateString) {
    if (!dateString) return 'Inconnu';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch {
        return dateString;
    }
}

function formatDateOnly(dateString) {
    if (!dateString) return 'Inconnu';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString();
    } catch {
        return dateString;
    }
}

function formatTimeOnly(dateString) {
    if (!dateString) return 'Inconnu';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleTimeString();
    } catch {
        return dateString;
    }
}

// Format port badges, handling comma-separated values
function formatPortBadges(portField) {
    if (!portField) return '<span class="badge port-badge">Inconnu</span>';
    
    // Split by comma and clean up whitespace
    const ports = portField.split(',').map(port => port.trim()).filter(port => port);
    
    if (ports.length === 1) {
        // Single port
        return `<span class="badge port-badge">${ports[0]}</span>`;
    } else if (ports.length > 1) {
        // Multiple ports - create multiple badges
        return `<span class="badge port-badge me-1">${ports[0]}</span><span class="badge port-badge">${ports[1]}</span>`;
    } else {
        return '<span class="badge port-badge">Inconnu</span>';
    }
}

// Format operator badges, handling comma-separated values
function formatOperatorBadges(operatorField) {
    if (!operatorField) return '<span class="badge operator-badge">Inconnu</span>';
    
    // Split by comma and clean up whitespace
    const operators = operatorField.split(',').map(operator => operator.trim()).filter(operator => operator);
    
    if (operators.length === 1) {
        // Single operator
        return `<span class="badge operator-badge">${operators[0]}</span>`;
    } else if (operators.length > 1) {
        // Multiple operators - create multiple badges
        return `<span class="badge operator-badge me-1">${operators[0]}</span><span class="badge operator-badge">${operators[1]}</span>`;
    } else {
        return '<span class="badge operator-badge">Inconnu</span>';
    }
}

// Format vessel type badges, handling comma-separated values
function formatVesselTypeBadges(vesselTypeField) {
    if (!vesselTypeField) return '<span class="badge vessel-type-badge">Inconnu</span>';
    
    // Split by comma and clean up whitespace
    const types = vesselTypeField.split(',').map(type => type.trim()).filter(type => type);
    
    if (types.length === 1) {
        // Single type
        return `<span class="badge vessel-type-badge">${types[0]}</span>`;
    } else if (types.length > 1) {
        // Multiple types - create multiple badges
        return `<span class="badge vessel-type-badge me-1">${types[0]}</span><span class="badge vessel-type-badge">${types[1]}</span>`;
    } else {
        return '<span class="badge vessel-type-badge">Inconnu</span>';
    }
}

function showLoading(show) {
    const page = document.querySelector('.page');
    if (show) {
        page.classList.add('loading');
    } else {
        page.classList.remove('loading');
    }
}

function showSuccess(message) {
    // Create success toast
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-success border-0';
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="ti ti-check me-2"></i>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Add to page and show
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove after hiding
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
}

function showError(message) {
    // Create error toast
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-danger border-0';
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="ti ti-alert-circle me-2"></i>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Add to page and show
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove after hiding
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
}
