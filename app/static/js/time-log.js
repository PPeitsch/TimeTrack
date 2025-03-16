document.addEventListener('DOMContentLoaded', function() {
    console.log('Time log script loaded');

    const yearSelect = document.getElementById('yearSelect');
    const monthSelect = document.getElementById('monthSelect');
    const logTable = document.getElementById('logTable');
    const prevMonthBtn = document.getElementById('prevMonth');
    const nextMonthBtn = document.getElementById('nextMonth');
    const prevYearBtn = document.getElementById('prevYear');
    const nextYearBtn = document.getElementById('nextYear');

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

    // Function to load monthly logs
    async function loadMonthlyLogs() {
        console.log('Loading monthly logs');
        const year = yearSelect.value;
        const month = monthSelect.value;

        try {
            console.log(`Fetching logs for ${year}/${month}`);
            const response = await fetch(`/logs/monthly/${year}/${month}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const logsData = await response.json();
            console.log('Logs data:', logsData);

            // Clear the table
            logTable.innerHTML = '';

            // Display log entries
            if (logsData.length === 0) {
                const row = document.createElement('tr');
                row.innerHTML = '<td colspan="4" class="text-center">No time entries found for this month</td>';
                logTable.appendChild(row);
            } else {
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
            console.error('Error loading logs:', error);
            logTable.innerHTML = `<tr><td colspan="4" class="text-center text-danger">Error loading data: ${error.message}</td></tr>`;
        }
    }

    // Navigation functions
    function navigateToPreviousMonth() {
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
        let year = parseInt(yearSelect.value);
        year--;

        if (year >= startYear) {
            yearSelect.value = year;
            loadMonthlyLogs();
        }
    }

    function navigateToNextYear() {
        let year = parseInt(yearSelect.value);
        year++;

        if (year <= endYear) {
            yearSelect.value = year;
            loadMonthlyLogs();
        }
    }

    // Add navigation button event listeners
    prevMonthBtn.addEventListener('click', navigateToPreviousMonth);
    nextMonthBtn.addEventListener('click', navigateToNextMonth);
    prevYearBtn.addEventListener('click', navigateToPreviousYear);
    nextYearBtn.addEventListener('click', navigateToNextYear);

    // Load data when changing year or month manually
    yearSelect.addEventListener('change', loadMonthlyLogs);
    monthSelect.addEventListener('change', loadMonthlyLogs);

    // Initial data load
    loadMonthlyLogs();
});