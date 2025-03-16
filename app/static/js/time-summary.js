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

    // Function to load monthly data
    async function loadMonthlyData() {
        console.log('Loading monthly data');
        const year = yearSelect.value;
        const month = monthSelect.value;

        try {
            console.log(`Fetching data for ${year}/${month}`);
            const response = await fetch(`/summary/monthly/${year}/${month}`);

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
            console.error('Error loading monthly data:', error);
            alert(`Error loading data: ${error.message}`);
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

        for (let day = 1; day <= daysInMonth; day++) {
            const date = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
            const dayOfWeek = new Date(year, month - 1, day).getDay();

            // Skip weekends (0 = Sunday, 6 = Saturday)
            const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;

            try {
                console.log(`Fetching data for day: ${date}`);
                const response = await fetch(`/summary/daily/${date}`);

                let dayData;
                if (response.ok) {
                    dayData = await response.json();
                    console.log(`Day data for ${date}:`, dayData);
                } else {
                    console.warn(`No data for ${date}, using defaults`);
                    // Default data if not found
                    dayData = {
                        hours: 0,
                        required: isWeekend ? 0 : 8,
                        difference: isWeekend ? 0 : -8,
                        absence_code: null
                    };
                }

                // Create table row
                const row = document.createElement('tr');

                // Format the date
                const formattedDate = new Date(date).toLocaleDateString();

                // Add row class for weekends
                if (isWeekend) {
                    row.classList.add('table-secondary');
                }

                // Determine type (Work Day, Absence, Weekend)
                let type = "Work Day";
                if (isWeekend) {
                    type = "Weekend";
                } else if (dayData.absence_code) {
                    type = dayData.absence_code;
                }

                // Calculate balance and add appropriate class
                const hours = dayData.hours || 0;
                const required = dayData.required || 0;
                const balance = hours - required;
                const balanceClass = balance >= 0 ? 'balance-positive' : 'balance-negative';

                row.innerHTML = `
                    <td>${formattedDate}</td>
                    <td>${type}</td>
                    <td>${hours.toFixed(1)}</td>
                    <td>${required.toFixed(1)}</td>
                    <td class="${balanceClass}">${balance.toFixed(1)}</td>
                `;

                timeTable.appendChild(row);

            } catch (error) {
                console.error(`Error loading data for ${date}:`, error);
            }
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
            loadMonthlyData();
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
            loadMonthlyData();
        }
    }

    function navigateToPreviousYear() {
        let year = parseInt(yearSelect.value);
        year--;

        if (year >= startYear) {
            yearSelect.value = year;
            loadMonthlyData();
        }
    }

    function navigateToNextYear() {
        let year = parseInt(yearSelect.value);
        year++;

        if (year <= endYear) {
            yearSelect.value = year;
            loadMonthlyData();
        }
    }

    // Add navigation button event listeners
    prevMonthBtn.addEventListener('click', navigateToPreviousMonth);
    nextMonthBtn.addEventListener('click', navigateToNextMonth);
    prevYearBtn.addEventListener('click', navigateToPreviousYear);
    nextYearBtn.addEventListener('click', navigateToNextYear);

    // Load data when changing year or month manually
    yearSelect.addEventListener('change', loadMonthlyData);
    monthSelect.addEventListener('change', loadMonthlyData);

    // Initial data load
    console.log('Initiating initial data load');
    loadMonthlyData();
});