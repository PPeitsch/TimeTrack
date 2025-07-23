document.addEventListener('DOMContentLoaded', function() {
    console.log('Time log script loaded');

    const yearSelect = document.getElementById('yearSelect');
    const monthSelect = document.getElementById('monthSelect');
    const logTable = document.getElementById('logTable');
    const prevMonthBtn = document.getElementById('prevMonth');
    const nextMonthBtn = document.getElementById('nextMonth');
    const prevYearBtn = document.getElementById('prevYear');
    const nextYearBtn = document.getElementById('nextYear');

    // Variable para controlar solicitudes simultáneas
    let currentRequest = null;
    let isLoading = false;

    // Initialize select elements if they exist
    if (!yearSelect || !monthSelect || !logTable) {
        console.error('Required DOM elements not found');
        return;
    }

    // Populate all months in the dropdown
    const months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];

    // Clear and repopulate the month select
    monthSelect.innerHTML = '';
    months.forEach((month, index) => {
        const option = document.createElement('option');
        option.value = index + 1;
        option.textContent = month;
        monthSelect.appendChild(option);
    });

    // Set current month as default
    const currentDate = new Date();
    monthSelect.value = currentDate.getMonth() + 1;

    // Set current year and add additional years
    const currentYear = currentDate.getFullYear();
    yearSelect.innerHTML = '';

    const startYear = currentYear - 3;
    const endYear = currentYear + 3;

    for (let year = startYear; year <= endYear; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelect.appendChild(option);
    }
    yearSelect.value = currentYear;

    // Function to show loading state
    function showLoading() {
        isLoading = true;
        // Disable navigation controls
        prevMonthBtn.disabled = true;
        nextMonthBtn.disabled = true;
        prevYearBtn.disabled = true;
        nextYearBtn.disabled = true;
        yearSelect.disabled = true;
        monthSelect.disabled = true;

        // Change cursor to indicate loading
        document.body.style.cursor = 'wait';

        // Show loading indicator
        logTable.innerHTML = '<tr><td colspan="4" class="text-center">Loading data...</td></tr>';
    }

    // Function to hide loading state
    function hideLoading() {
        isLoading = false;
        // Enable navigation controls
        prevMonthBtn.disabled = false;
        nextMonthBtn.disabled = false;
        prevYearBtn.disabled = false;
        nextYearBtn.disabled = false;
        yearSelect.disabled = false;
        monthSelect.disabled = false;

        // Reset cursor
        document.body.style.cursor = 'default';
    }

    // Function to load monthly logs
    async function loadMonthlyLogs() {
        // Prevent multiple simultaneous requests
        if (isLoading) {
            console.log('Already loading data, request ignored');
            return;
        }

        showLoading();

        console.log('Loading monthly logs');
        const year = yearSelect.value;
        const month = monthSelect.value;

        try {
            console.log(`Fetching logs for ${year}/${month}`);

            // Cancel any existing request
            if (currentRequest) {
                currentRequest.abort();
            }

            // Use fetch with AbortController
            const controller = new AbortController();
            const signal = controller.signal;
            currentRequest = controller;

            const response = await fetch(`/logs/monthly/${year}/${month}`, { signal });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const logsData = await response.json();
            console.log('Logs data:', logsData);

            // Display log entries
            if (logsData.length === 0) {
                logTable.innerHTML = '<tr><td colspan="4" class="text-center">No time entries found for this month</td></tr>';
            } else {
                logTable.innerHTML = '';
                logsData.forEach(log => {
                    const row = document.createElement('tr');

                    // Format date
                    const date = new Date(log.date);
                    const formattedDate = date.toLocaleDateString();

                    // Format entries
                    let entriesHtml = '';
                    if (log.type !== 'Work Day' || log.entries.length === 0) {
                        entriesHtml = '<em>No time entries</em>';
                    } else {
                        entriesHtml = '<ul class="mb-0">';
                        log.entries.forEach(entry => {
                            entriesHtml += `<li>${entry.entry} - ${entry.exit}</li>`;
                        });
                        entriesHtml += '</ul>';
                    }

                    row.innerHTML = `
                        <td>${formattedDate}</td>
                        <td>${log.type}</td>
                        <td>${entriesHtml}</td>
                        <td>${log.total_hours.toFixed(1)}</td>
                    `;

                    logTable.appendChild(row);
                });
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Fetch aborted');
            } else {
                console.error('Error loading logs:', error);
                logTable.innerHTML = `<tr><td colspan="4" class="text-center text-danger">Error loading data: ${error.message}</td></tr>`;
            }
        } finally {
            hideLoading();
            currentRequest = null;
        }
    }

    // Navigation functions with throttling
    function throttle(func, delay) {
        let lastCall = 0;
        return function(...args) {
            const now = new Date().getTime();
            if (now - lastCall < delay) {
                return;
            }
            lastCall = now;
            return func(...args);
        };
    }

    function navigateToPreviousMonth() {
        if (isLoading) return;

        let month = parseInt(monthSelect.value);
        let year = parseInt(yearSelect.value);

        month--;
        if (month < 1) {
            month = 12;
            year--;
        }

        if (year >= startYear) {
            monthSelect.value = month;
            yearSelect.value = year;
            loadMonthlyLogs();
        }
    }

    function navigateToNextMonth() {
        if (isLoading) return;

        let month = parseInt(monthSelect.value);
        let year = parseInt(yearSelect.value);

        month++;
        if (month > 12) {
            month = 1;
            year++;
        }

        if (year <= endYear) {
            monthSelect.value = month;
            yearSelect.value = year;
            loadMonthlyLogs();
        }
    }

    function navigateToPreviousYear() {
        if (isLoading) return;

        let year = parseInt(yearSelect.value);
        year--;

        if (year >= startYear) {
            yearSelect.value = year;
            loadMonthlyLogs();
        }
    }

    function navigateToNextYear() {
        if (isLoading) return;

        let year = parseInt(yearSelect.value);
        year++;

        if (year <= endYear) {
            yearSelect.value = year;
            loadMonthlyLogs();
        }
    }

    // Add navigation button event listeners with throttling
    prevMonthBtn.addEventListener('click', throttle(navigateToPreviousMonth, 300));
    nextMonthBtn.addEventListener('click', throttle(navigateToNextMonth, 300));
    prevYearBtn.addEventListener('click', throttle(navigateToPreviousYear, 300));
    nextYearBtn.addEventListener('click', throttle(navigateToNextYear, 300));

    // Load data when changing year or month manually
    yearSelect.addEventListener('change', loadMonthlyLogs);
    monthSelect.addEventListener('change', loadMonthlyLogs);

    // Initial data load
    loadMonthlyLogs();
});
