document.addEventListener('DOMContentLoaded', function() {
    // Selectors
    const yearSelect = document.getElementById('yearSelect');
    const monthSelect = document.getElementById('monthSelect');
    const calendarGrid = document.getElementById('calendarGrid');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const prevMonthBtn = document.getElementById('prevMonth');
    const nextMonthBtn = document.getElementById('nextMonth');
    const prevYearBtn = document.getElementById('prevYear');
    const nextYearBtn = document.getElementById('nextYear');
    const editDayModalEl = document.getElementById('editDayModal');
    const editDayModal = new bootstrap.Modal(editDayModalEl);
    const selectedDateEl = document.getElementById('selectedDate');
    const dayTypeSelect = document.getElementById('dayTypeSelect');
    const dayTypeSelectLabel = document.getElementById('dayTypeSelectLabel');
    const saveDayTypeBtn = document.getElementById('saveDayTypeBtn');

    let currentDate = new Date();
    let selectedDates = [];
    let isMouseDown = false;
    let absenceCodes = [];

    async function fetchAbsenceCodes() {
        try {
            const response = await fetch('/monthly-log/api/absence-codes');
            if (!response.ok) throw new Error('Failed to fetch absence codes');
            absenceCodes = await response.json();
        } catch (error) {
            console.error(error);
        }
    }

    function populateDayTypeSelect() {
        dayTypeSelect.innerHTML = '';
        // Add special "Default" option first
        dayTypeSelect.add(new Option("(Revert to Default)", "DEFAULT"));
        dayTypeSelect.add(new Option("Work Day", "Work Day"));

        if (absenceCodes && absenceCodes.length > 0) {
            absenceCodes.forEach(code => {
                dayTypeSelect.add(new Option(code.replace(/_/g, ' '), code));
            });
        }
    }

    // ... (el resto de las funciones de JS no cambian)

    function populateSelectors() {
        const currentYear = new Date().getFullYear();
        const startYear = currentYear - 5;
        const endYear = currentYear + 5;
        yearSelect.innerHTML = '';
        for (let year = startYear; year <= endYear; year++) yearSelect.add(new Option(year, year));
        const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
        monthSelect.innerHTML = '';
        months.forEach((month, index) => monthSelect.add(new Option(month, index)));
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
            for (let i = 0; i < startDayOfWeek; i++) {
                const blankCell = document.createElement('div');
                blankCell.classList.add('day-cell', 'blank');
                calendarGrid.appendChild(blankCell);
            }
            for (let day = 1; day <= daysInMonth; day++) {
                const dayCell = document.createElement('div');
                const date = new Date(year, month, day);
                const dateStr = date.toISOString().split('T')[0];
                const dayType = daysMap.get(dateStr) || 'Work Day';
                dayCell.classList.add('day-cell');
                dayCell.dataset.date = dateStr;
                dayCell.addEventListener('mousedown', (e) => handleMouseDown(e.currentTarget));
                dayCell.addEventListener('mouseover', (e) => handleMouseOver(e.currentTarget));
                dayCell.innerHTML = `<div class="day-number">${day}</div><div class="day-type">${dayType.replace(/_/g, ' ')}</div>`;
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

    function handleMouseDown(cell) {
        if (cell.classList.contains('blank')) return;
        isMouseDown = true;
        clearSelection();
        toggleSelection(cell);
    }

    function handleMouseOver(cell) {
        if (!isMouseDown || cell.classList.contains('blank')) return;
        toggleSelection(cell);
    }

    function handleMouseUp() {
        if (!isMouseDown) return;
        isMouseDown = false;
        openEditModal();
    }

    function toggleSelection(cell) {
        cell.classList.toggle('day-selected');
        const date = cell.dataset.date;
        if (cell.classList.contains('day-selected')) {
            if (!selectedDates.includes(date)) selectedDates.push(date);
        } else {
            selectedDates = selectedDates.filter(d => d !== date);
        }
    }

    function clearSelection() {
        selectedDates = [];
        document.querySelectorAll('.day-selected').forEach(cell => cell.classList.remove('day-selected'));
    }

    function openEditModal() {
        if (selectedDates.length === 0) return;
        if (selectedDates.length === 1) {
            selectedDateEl.textContent = new Date(selectedDates[0].replace(/-/g, '/')).toLocaleDateString();
            const cell = calendarGrid.querySelector(`[data-date="${selectedDates[0]}"]`);
            const currentType = cell.querySelector('.day-type').textContent;
            dayTypeSelectLabel.textContent = `Change Type (Current: ${currentType})`;
        } else {
            selectedDateEl.textContent = `${selectedDates.length} days selected`;
            dayTypeSelectLabel.textContent = 'Set New Type for All Selected Days';
        }
        editDayModal.show();
    }

    async function saveDayType() {
        if (selectedDates.length === 0) return;
        const newDayType = dayTypeSelect.value;
        try {
            const response = await fetch('/monthly-log/api/update-days', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ dates: selectedDates, day_type: newDayType })
            });
            if (!response.ok) throw new Error('Failed to save changes');
            editDayModal.hide();
            clearSelection();
            await renderCalendar();
        } catch (error) {
            console.error(error);
            alert('Error saving changes. Please try again.');
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

    // Event Listeners
    prevMonthBtn.addEventListener('click', () => changeMonth(-1));
    nextMonthBtn.addEventListener('click', () => changeMonth(1));
    prevYearBtn.addEventListener('click', () => changeYear(-1));
    nextYearBtn.addEventListener('click', () => changeYear(1));
    yearSelect.addEventListener('change', () => { currentDate.setFullYear(parseInt(yearSelect.value)); renderCalendar(); });
    monthSelect.addEventListener('change', () => { currentDate.setMonth(parseInt(monthSelect.value)); renderCalendar(); });
    saveDayTypeBtn.addEventListener('click', saveDayType);
    document.addEventListener('mouseup', handleMouseUp);
    editDayModalEl.addEventListener('hidden.bs.modal', clearSelection);

    async function init() {
        populateSelectors();
        updateSelectors();
        await fetchAbsenceCodes();
        populateDayTypeSelect();
        await renderCalendar();
    }

    init();
});
