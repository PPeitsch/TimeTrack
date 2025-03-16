document.addEventListener('DOMContentLoaded', function() {
    const yearSelect = document.getElementById('yearSelect');
    const monthSelect = document.getElementById('monthSelect');
    const timeTable = document.getElementById('timeTable');
    const monthlyRequired = document.getElementById('monthlyRequired');
    const monthlyCompleted = document.getElementById('monthlyCompleted');
    const monthlyBalance = document.getElementById('monthlyBalance');

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

    for (let year = currentYear - 1; year <= currentYear + 1; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelect.appendChild(option);
    }
    yearSelect.value = currentYear;

    // Function to load monthly data
    async function loadMonthlyData() {
        const year = yearSelect.value;
        const month = monthSelect.value;

        try {
            const response = await fetch(`/analysis/monthly/${year}/${month}`);
            if (!response.ok) throw new Error('Failed to fetch monthly data');

            const monthlyData = await response.json();

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
        }
    }

    // Function to load daily data for the month
    async function loadDailyData(year, month) {
        // Clear table first
        timeTable.innerHTML = '';

        const daysInMonth = new Date(year, month, 0).getDate();

        for (let day = 1; day <= daysInMonth; day++) {
            const date = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
            const dayOfWeek = new Date(year, month - 1, day).getDay();

            // Skip weekends (0 = Sunday, 6 = Saturday)
            const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
            const requiredHours = isWeekend ? 0 : 8;

            try {
                const response = await fetch(`/analysis/daily/${date}`);
                if (!response.ok) throw new Error(`Failed to fetch data for ${date}`);

                const dayData = await response.json();

                // Create table row
                const row = document.createElement('tr');

                // Format the date as day/month/year
                const formattedDate = new Date(date).toLocaleDateString('en-GB');

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
                const balance = dayData.hours - dayData.required;
                const balanceClass = balance >= 0 ? 'balance-positive' : 'balance-negative';

                row.innerHTML = `
                    <td>${formattedDate}</td>
                    <td>${type}</td>
                    <td>${dayData.hours.toFixed(1)}</td>
                    <td>${dayData.required.toFixed(1)}</td>
                    <td class="${balanceClass}">${balance.toFixed(1)}</td>
                `;

                timeTable.appendChild(row);

            } catch (error) {
                // If no data exists for this day, create a default row
                const row = document.createElement('tr');

                // Format the date
                const formattedDate = new Date(date).toLocaleDateString('en-GB');

                // Add row class for weekends
                if (isWeekend) {
                    row.classList.add('table-secondary');

                    row.innerHTML = `
                        <td>${formattedDate}</td>
                        <td>Weekend</td>
                        <td>0.0</td>
                        <td>0.0</td>
                        <td>0.0</td>
                    `;
                } else {
                    row.innerHTML = `
                        <td>${formattedDate}</td>
                        <td>Work Day</td>
                        <td>0.0</td>
                        <td>8.0</td>
                        <td class="balance-negative">-8.0</td>
                    `;
                }

                timeTable.appendChild(row);
            }
        }
    }

    // Load data when changing year or month
    yearSelect.addEventListener('change', loadMonthlyData);
    monthSelect.addEventListener('change', loadMonthlyData);

    // Initial data load
    loadMonthlyData();
});