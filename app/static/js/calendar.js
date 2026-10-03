// Calendar screen: month grid, single-day editor and bulk editor.
document.addEventListener('DOMContentLoaded', function () {
    const grid = document.getElementById('calendarGrid');
    const monthTitle = document.getElementById('monthTitle');
    const loading = document.getElementById('loadingIndicator');
    const dayPanel = new bootstrap.Offcanvas(document.getElementById('dayPanel'));
    const bulkPanel = new bootstrap.Offcanvas(document.getElementById('bulkPanel'));
    const dayForm = document.getElementById('dayForm');
    const timeRows = document.getElementById('timeRows');
    const rowTemplate = document.getElementById('timeRowTemplate');
    const absenceSelect = document.getElementById('absenceSelect');
    const observation = document.getElementById('observation');
    const dayError = document.getElementById('dayError');
    const bulkType = document.getElementById('bulkType');

    // Dates follow the page language, not the browser's.
    const LOCALE = document.documentElement.lang || undefined;
    let current = new Date();
    current.setDate(1);
    let daysByDate = new Map();
    let absenceCodes = [];
    let editingDate = null;
    let selection = new Set();
    let dragging = false;
    let dragMoved = false;
    let anchorDate = null;

    // ---------- Data ----------

    async function loadCodes() {
        try {
            const response = await fetch('/settings/api/absence-codes');
            absenceCodes = response.ok ? await response.json() : [];
        } catch (error) {
            absenceCodes = [];
        }
        absenceSelect.innerHTML = '';
        absenceCodes.forEach(c => absenceSelect.add(new Option(c.code, c.code)));
        document.getElementById('noCodesHint').hidden = absenceCodes.length > 0;

        bulkType.innerHTML = '';
        bulkType.add(new Option(t('default_option'), 'DEFAULT'));
        bulkType.add(new Option(t('Work Day'), 'Work Day'));
        absenceCodes.forEach(c => bulkType.add(new Option(c.code, c.code)));
    }

    async function loadMonth() {
        loading.hidden = false;
        const year = current.getFullYear();
        const month = current.getMonth();
        const title = current.toLocaleDateString(LOCALE, { month: 'long', year: 'numeric' });
        monthTitle.textContent = title.charAt(0).toUpperCase() + title.slice(1);
        try {
            const response = await fetch(`/api/days/${year}/${month + 1}`);
            if (!response.ok) throw new Error(t('load_calendar_error'));
            const data = await response.json();
            daysByDate = new Map(data.days.map(d => [d.date, d]));
            renderGrid(year, month);
            renderSummary(data.summary);
        } catch (error) {
            grid.innerHTML = '';
            showToast(error.message, 'error');
        } finally {
            loading.hidden = true;
        }
    }

    // ---------- Rendering ----------

    function typeClass(type) {
        if (type === 'Work Day') return 'day-work';
        if (type === 'Weekend') return 'day-weekend';
        if (type === 'Holiday') return 'day-holiday';
        return 'day-absence';
    }

    function renderGrid(year, month) {
        grid.innerHTML = '';
        const first = new Date(year, month, 1);
        const offset = (first.getDay() + 6) % 7; // Monday first
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const todayStr = isoDate(new Date());

        for (let i = 0; i < offset; i++) {
            const blank = document.createElement('div');
            blank.className = 'day-cell blank';
            blank.setAttribute('aria-hidden', 'true');
            grid.appendChild(blank);
        }
        for (let n = 1; n <= daysInMonth; n++) {
            const dateStr = isoDate(new Date(year, month, n));
            const day = daysByDate.get(dateStr);
            const cell = document.createElement('button');
            cell.type = 'button';
            cell.className = `day-cell ${typeClass(day.type)}`;
            if (dateStr === todayStr) cell.classList.add('day-today');
            if (selection.has(dateStr)) cell.classList.add('day-selected');
            cell.dataset.date = dateStr;

            const label = [t(day.type)];
            if (day.worked) label.push(t('worked', { hours: formatHours(day.worked) }));
            if (day.observation) label.push(day.observation);
            cell.setAttribute('aria-label', `${n}: ${label.join(', ')}`);

            // Work on a weekend or holiday keeps the base type visible (overtime).
            let badge = '';
            if (day.type !== 'Work Day') badge = day.type;
            else if (day.base_type !== 'Work Day') badge = day.base_type;
            if (day.type === 'Work Day' && day.base_type !== 'Work Day') cell.classList.add('day-overtime');
            cell.innerHTML =
                `<span class="day-number">${n}</span>` +
                (badge ? `<span class="day-type">${escapeHTML(t(badge))}</span>` : '') +
                (day.worked ? `<span class="day-hours">${formatHours(day.worked)}</span>` : '') +
                (day.observation ? `<span class="day-note" title="${escapeHTML(t('has_observation'))}">${icon('note')}</span>` : '');
            grid.appendChild(cell);
        }
    }

    function renderSummary(summary) {
        document.getElementById('sumWorked').textContent = formatHours(summary.total);
        document.getElementById('sumRequired').textContent = formatHours(summary.required);
        const balance = document.getElementById('sumBalance');
        balance.textContent = (summary.difference > 0 ? '+' : '') + formatHours(summary.difference);
        balance.className = summary.difference >= 0 ? 'balance-positive' : 'balance-negative';
    }

    // ---------- Single day editor ----------

    function addTimeRow(entry = '', exit = '') {
        const row = rowTemplate.content.firstElementChild.cloneNode(true);
        row.querySelector('.time-entry-input').value = entry;
        row.querySelector('.time-exit-input').value = exit;
        row.querySelector('.remove-row').addEventListener('click', () => { row.remove(); updateWorkedPreview(); });
        row.querySelectorAll('input').forEach(i => i.addEventListener('input', updateWorkedPreview));
        timeRows.appendChild(row);
    }

    function collectEntries() {
        return [...timeRows.querySelectorAll('.time-row')]
            .map(r => ({ entry: r.querySelector('.time-entry-input').value, exit: r.querySelector('.time-exit-input').value }))
            .filter(e => e.entry || e.exit);
    }

    function updateWorkedPreview() {
        let total = 0;
        collectEntries().forEach(e => {
            if (e.entry && e.exit && e.exit > e.entry) {
                const [h1, m1] = e.entry.split(':').map(Number);
                const [h2, m2] = e.exit.split(':').map(Number);
                total += (h2 * 60 + m2 - h1 * 60 - m1) / 60;
            }
        });
        document.getElementById('workedPreview').textContent = total ? t('worked', { hours: formatHours(total) }) : '';
    }

    function selectedKind() {
        return dayForm.querySelector('input[name="kind"]:checked').value;
    }

    function updateKindFields() {
        const kind = selectedKind();
        document.getElementById('workFields').hidden = kind !== 'work';
        document.getElementById('absenceFields').hidden = kind !== 'absence';
    }

    function openDay(dateStr) {
        const day = daysByDate.get(dateStr);
        if (!day) return;
        editingDate = dateStr;
        const date = new Date(dateStr + 'T00:00:00');
        document.getElementById('dayPanelTitle').textContent =
            date.toLocaleDateString(LOCALE, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
        dayError.hidden = true;

        let kind = 'default';
        if (day.absence_code) kind = 'absence';
        else if (day.has_entry || day.base_type === 'Work Day') kind = 'work';
        dayForm.querySelector(`input[name="kind"][value="${kind}"]`).checked = true;
        timeRows.innerHTML = '';
        (day.entries.length ? day.entries : [{ entry: '', exit: '' }]).forEach(e => addTimeRow(e.entry, e.exit));
        if (day.absence_code) absenceSelect.value = day.absence_code;
        observation.value = day.observation || '';
        document.getElementById('baseTypeHint').textContent =
            t('default_hint', { type: t(day.base_type) });
        updateKindFields();
        updateWorkedPreview();
        dayPanel.show();
    }

    async function saveDay(event) {
        event.preventDefault();
        const kind = selectedKind();
        const payload = { kind, observation: observation.value };
        if (kind === 'work') payload.entries = collectEntries();
        if (kind === 'absence') payload.absence_code = absenceSelect.value;

        try {
            const response = await fetch(`/api/days/${editingDate}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || t('save_day_error'));
            dayPanel.hide();
            showToast(t('day_saved'));
            await loadMonth();
        } catch (error) {
            dayError.textContent = error.message;
            dayError.hidden = false;
        }
    }

    // ---------- Selection and bulk editor ----------

    function setSelection(dates) {
        selection = new Set(dates);
        grid.querySelectorAll('.day-cell[data-date]').forEach(c =>
            c.classList.toggle('day-selected', selection.has(c.dataset.date)));
    }

    function rangeBetween(a, b) {
        const [start, end] = a <= b ? [a, b] : [b, a];
        return [...daysByDate.keys()].filter(d => d >= start && d <= end);
    }

    function openBulk() {
        document.getElementById('bulkPanelTitle').textContent = t('days_selected', { count: selection.size });
        bulkPanel.show();
    }

    async function saveBulk() {
        try {
            const response = await fetch('/monthly-log/api/update-days', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ dates: [...selection], day_type: bulkType.value }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || t('save_changes_error'));
            bulkPanel.hide();
            showToast(t('days_updated', { count: selection.size }));
            await loadMonth();
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    grid.addEventListener('mousedown', e => {
        const cell = e.target.closest('.day-cell[data-date]');
        if (!cell || e.button !== 0) return;
        if (e.shiftKey && anchorDate) {
            e.preventDefault();
            setSelection(rangeBetween(anchorDate, cell.dataset.date));
            openBulk();
            return;
        }
        dragging = true;
        dragMoved = false;
        anchorDate = cell.dataset.date;
        setSelection([anchorDate]);
    });

    grid.addEventListener('mouseover', e => {
        const cell = e.target.closest('.day-cell[data-date]');
        if (!dragging || !cell) return;
        if (cell.dataset.date !== anchorDate) dragMoved = true;
        setSelection(rangeBetween(anchorDate, cell.dataset.date));
    });

    document.addEventListener('mouseup', () => {
        if (!dragging) return;
        dragging = false;
        if (dragMoved && selection.size > 1) openBulk();
    });

    // Click (mouse without drag, or keyboard Enter/Space) opens the day editor.
    grid.addEventListener('click', e => {
        const cell = e.target.closest('.day-cell[data-date]');
        if (!cell || e.shiftKey) return;
        if (dragMoved) { dragMoved = false; return; }
        anchorDate = cell.dataset.date;
        setSelection([anchorDate]);
        openDay(cell.dataset.date);
    });

    // ---------- Wiring ----------

    function changeMonth(offset) {
        current = new Date(current.getFullYear(), current.getMonth() + offset, 1);
        setSelection([]);
        loadMonth();
    }

    document.getElementById('prevMonth').addEventListener('click', () => changeMonth(-1));
    document.getElementById('nextMonth').addEventListener('click', () => changeMonth(1));
    document.getElementById('todayBtn').addEventListener('click', () => {
        const now = new Date();
        current = new Date(now.getFullYear(), now.getMonth(), 1);
        loadMonth();
    });
    document.getElementById('addTimeRow').addEventListener('click', () => addTimeRow());
    dayForm.querySelectorAll('input[name="kind"]').forEach(r => r.addEventListener('change', updateKindFields));
    dayForm.addEventListener('submit', saveDay);
    document.getElementById('saveBulk').addEventListener('click', saveBulk);
    document.getElementById('dayPanel').addEventListener('hidden.bs.offcanvas', () => setSelection([]));
    document.getElementById('bulkPanel').addEventListener('hidden.bs.offcanvas', () => setSelection([]));

    async function init() {
        const requested = new URLSearchParams(window.location.search).get('day');
        if (requested && /^\d{4}-\d{2}-\d{2}$/.test(requested)) {
            const d = new Date(requested + 'T00:00:00');
            current = new Date(d.getFullYear(), d.getMonth(), 1);
        }
        await loadCodes();
        await loadMonth();
        if (requested && daysByDate.has(requested)) openDay(requested);
    }

    init();
});
