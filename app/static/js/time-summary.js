document.addEventListener('DOMContentLoaded', function() {
    console.log('Time summary script loaded');

    const yearSelect = document.getElementById('yearSelect');
    const monthSelect = document.getElementById('monthSelect');
    const timeTable = document.getElementById('timeTable');
    const monthlyRequired = document.getElementById('monthlyRequired');
    const monthlyCompleted = document.getElementById('monthlyCompleted');
    const monthlyBalance = document.getElementById('monthlyBalance');
    const prevMonthBtn = document.getElementById('prevMonth');
    const nextMonthBtn = document.getElementById('nextMonth');
    const prevYearBtn = document.getElementById('prevYear');
    const nextYearBtn = document.getElementById('nextYear');

    // Variable para almacenar la solicitud AJAX actual
    let currentRequest = null;
    // Variable para controlar si estamos en medio de una carga
    let isLoading = false;

    // Initialize select elements if they exist
    if (!yearSelect || !monthSelect || !timeTable) {
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
        // Disable navigation buttons
        prevMonthBtn.disabled = true;
        nextMonthBtn.disabled = true;
        prevYearBtn.disabled = true;
        nextYearBtn.disabled = true;
        yearSelect.disabled = true;
        monthSelect.disabled = true;

        // Change cursor to indicate loading
        document.body.style.cursor = 'wait';

        // Show loading indicator in the table
        timeTable.innerHTML = '<tr><td colspan="5" class="text-center">Loading data...</td></tr>';
    }

    // Function to hide loading state
    function hideLoading() {
        isLoading = false;
        // Enable navigation buttons
        prevMonthBtn.disabled = false;
        nextMonthBtn.disabled = false;
        prevYearBtn.disabled = false;
        nextYearBtn.disabled = false;
        yearSelect.disabled = false;
        monthSelect.disabled = false;

        // Reset cursor
        document.body.style.cursor = 'default';
    }

    // Function to load monthly data
    async function loadMonthlyData() {
        // Prevent multiple simultaneous requests
        if (isLoading) {
            console.log('Already loading data, request ignored');
            return;
        }

        showLoading();

        console.log('Loading monthly data');
        const year = yearSelect.value;
        const month = monthSelect.value;

        try {
            console.log(`Fetching data for ${year}/${month}`);

            // Cancel any existing request
            if (currentRequest) {
                currentRequest.abort();
            }

            // Use the fetch API with AbortController
            const controller = new AbortController();
            const signal = controller.signal;
            currentRequest = controller;

            const response = await fetch(`/summary/monthly/${year}/${month}`, { signal });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const monthlyData = await response.json();
            console.log('Monthly data:', monthlyData);

            // Update monthly summary
            monthlyRequired.textContent = monthlyData.required.toFixed(1);
            monthlyCompleted.textContent = monthlyData.total.toFixed(1);

            const balance = monthlyData.difference;
            monthlyBalance.textContent = balance.toFixed(1);
            monthlyBalance.className = balance >= 0 ? 'balance-positive' : 'balance-negative';

            // Load daily data for the selected month
            await loadDailyData(year, month);
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Fetch aborted');
            } else {
                console.error('Error loading monthly data:', error);
                timeTable.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Error loading data: ${error.message}</td></tr>`;
            }
        } finally {
            hideLoading();
            currentRequest = null;
        }
    }

    // Function to load daily data for the month
    async function loadDailyData(year, month) {
        console.log(`Loading daily data for ${year}/${month}`);
        // Clear table first
        timeTable.innerHTML = '';

        // Get days in month
        const daysInMonth = new Date(year, month, 0).getDate();
        console.log(`Days in month: ${daysInMonth}`);

        // Create a batch of promises for all day requests
        const dayPromises = [];
        const dayData = [];

        for (let day = 1; day <= daysInMonth; day++) {
            const date = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
            const dayOfWeek = new Date(year, month - 1, day).getDay();
            const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;

            // Store date info to be used after fetching
            dayData.push({
                date: date,
                formattedDate: new Date(date).toLocaleDateString(),
                isWeekend: isWeekend,
                dayOfWeek: dayOfWeek
            });

            // Create the promise but don't await it yet
            const dayPromise = fetch(`/summary/daily/${date}`)
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        return {
                            hours: 0,
                            required: isWeekend ? 0 : 8,
                            difference: isWeekend ? 0 : -8,
                            absence_code: null
                        };
                    }
                })
                .catch(error => {
                    console.error(`Error loading data for ${date}:`, error);
                    return {
                        hours: 0,
                        required: isWeekend ? 0 : 8,
                        difference: isWeekend ? 0 : -8,
                        absence_code: null
                    };
                });

            dayPromises.push(dayPromise);
        }

        // Wait for all promises to resolve
        const dayResults = await Promise.all(dayPromises);

        // Now build the table with the results
        for (let i = 0; i < dayResults.length; i++) {
            const result = dayResults[i];
            const info = dayData[i];

            // Create table row
            const row = document.createElement('tr');

            // Add row class for weekends
            if (info.isWeekend) {
                row.classList.add('table-secondary');
            }

            // Determine type (Work Day, Absence, Weekend)
            let type = "Work Day";
            if (info.isWeekend) {
                type = "Weekend";
            } else if (result.absence_code) {
                type = result.absence_code;
            }

            // Calculate balance and add appropriate class
            const hours = result.hours || 0;
            const required = result.required || 0;
            const balance = hours - required;
            const balanceClass = balance >= 0 ? 'balance-positive' : 'balance-negative';

            row.innerHTML = `
                <td>${info.formattedDate}</td>
                <td>${type}</td>
                <td>${hours.toFixed(1)}</td>
                <td>${required.toFixed(1)}</td>
                <td class="${balanceClass}">${balance.toFixed(1)}</td>
            `;

            timeTable.appendChild(row);
        }
    }

    // Navigation functions
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
            loadMonthlyData();
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
            loadMonthlyData();
        }
    }

    function navigateToPreviousYear() {
        if (isLoading) return;

        let year = parseInt(yearSelect.value);
        year--;

        if (year >= startYear) {
            yearSelect.value = year;
            loadMonthlyData();
        }
    }

    function navigateToNextYear() {
        if (isLoading) return;

        let year = parseInt(yearSelect.value);
        year++;

        if (year <= endYear) {
            yearSelect.value = year;
            loadMonthlyData();
        }
    }

    // Throttle function to prevent too many rapid clicks
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

    // Add navigation button event listeners with throttling
    prevMonthBtn.addEventListener('click', throttle(navigateToPreviousMonth, 300));
    nextMonthBtn.addEventListener('click', throttle(navigateToNextMonth, 300));
    prevYearBtn.addEventListener('click', throttle(navigateToPreviousYear, 300));
    nextYearBtn.addEventListener('click', throttle(navigateToNextYear, 300));

    // Load data when changing year or month manually
    yearSelect.addEventListener('change', loadMonthlyData);
    monthSelect.addEventListener('change', loadMonthlyData);

    // Initial data load
    console.log('Initiating initial data load');
    loadMonthlyData();
});