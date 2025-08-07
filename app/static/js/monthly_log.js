document.addEventListener('DOMContentLoaded', function() {
    const yearSelect = document.getElementById('yearSelect');
    const monthSelect = document.getElementById('monthSelect');
    const calendarGrid = document.getElementById('calendarGrid');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const prevMonthBtn = document.getElementById('prevMonth');
    const nextMonthBtn = document.getElementById('nextMonth');
    const prevYearBtn = document.getElementById('prevYear');
    const nextYearBtn = document.getElementById('nextYear');

    let currentDate = new Date();

    function populateSelectors() {
        const currentYear = new Date().getFullYear();
        const startYear = currentYear - 5;
        const endYear = currentYear + 5;

        yearSelect.innerHTML = '';
        for (let year = startYear; year <= endYear; year++) {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            yearSelect.appendChild(option);
        }

        const months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ];
        monthSelect.innerHTML = '';
        months.forEach((month, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = month;
            monthSelect.appendChild(option);
        });
    }

    function updateSelectors() {
        yearSelect.value = currentDate.getFullYear();
        monthSelect.value = currentDate.getMonth();
    }

    async function renderCalendar() {
        loadingIndicator.style.display = 'block';
        calendarGrid.innerHTML = '';

        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();

        try {
            const response = await fetch(`/monthly-log/api/${year}/${month + 1}`);
            if (!response.ok) throw new Error('Failed to fetch calendar data');
            const daysData = await response.json();
            const daysMap = new Map(daysData.map(d => [d.date, d.type]));

            const firstDayOfMonth = new Date(year, month, 1);
            const daysInMonth = new Date(year, month + 1, 0).getDate();
            const startDayOfWeek = firstDayOfMonth.getDay();

            // Create blank cells for days before the first of the month
            for (let i = 0; i < startDayOfWeek; i++) {
                const blankCell = document.createElement('div');
                blankCell.classList.add('day-cell', 'blank');
                calendarGrid.appendChild(blankCell);
            }

            // Create cells for each day of the month
            for (let day = 1; day <= daysInMonth; day++) {
                const dayCell = document.createElement('div');
                const date = new Date(year, month, day);
                const dateStr = date.toISOString().split('T')[0];
                const dayType = daysMap.get(dateStr) || 'Work Day';

                dayCell.classList.add('day-cell');
                dayCell.dataset.date = dateStr;
                dayCell.innerHTML = `
                    <div class="day-number">${day}</div>
                    <div class="day-type">${dayType.replace(/_/g, ' ')}</div>
                `;

                // Add class based on day type for styling
                dayCell.classList.add(`day-${dayType.toLowerCase().split(' ')[0]}`);

                calendarGrid.appendChild(dayCell);
            }
        } catch (error) {
            console.error(error);
            calendarGrid.innerHTML = '<div class="alert alert-danger">Could not load calendar data.</div>';
        } finally {
            loadingIndicator.style.display = 'none';
        }
    }

    function changeMonth(offset) {
        currentDate.setMonth(currentDate.getMonth() + offset);
        updateSelectors();
        renderCalendar();
    }

    function changeYear(offset) {
        currentDate.setFullYear(currentDate.getFullYear() + offset);
        updateSelectors();
        renderCalendar();
    }

    prevMonthBtn.addEventListener('click', () => changeMonth(-1));
    nextMonthBtn.addEventListener('click', () => changeMonth(1));
    prevYearBtn.addEventListener('click', () => changeYear(-1));
    nextYearBtn.addEventListener('click', () => changeYear(1));
    yearSelect.addEventListener('change', () => {
        currentDate.setFullYear(parseInt(yearSelect.value));
        renderCalendar();
    });
    monthSelect.addEventListener('change', () => {
        currentDate.setMonth(parseInt(monthSelect.value));
        renderCalendar();
    });

    populateSelectors();
    updateSelectors();
    renderCalendar();
});
