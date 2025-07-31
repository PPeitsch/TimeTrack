document.addEventListener('DOMContentLoaded', function() {
    console.log('Entry handlers script loaded');

    // Get primary elements
    const dateInput = document.getElementById('date');
    const entryTypeSelect = document.getElementById('entryType');
    const workDayFields = document.getElementById('workDayFields');
    const entryForm = document.getElementById('entryForm');

    // Function to toggle visibility of time entry fields
    function toggleWorkDayFields() {
        if (!entryTypeSelect || !workDayFields) return;

        if (entryTypeSelect.value === 'WORK') {
            workDayFields.style.display = 'block';
        } else {
            workDayFields.style.display = 'none';
        }
    }

    // Set current date as default
    if (dateInput) {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        dateInput.value = `${year}-${month}-${day}`;
    }

    // Add event listener to the type dropdown
    if (entryTypeSelect) {
        entryTypeSelect.addEventListener('change', toggleWorkDayFields);
    }

    // Function to handle remove button clicks
    function handleRemoveClick(event) {
        console.log('Remove button clicked');
        const timeEntriesContainer = document.getElementById('timeEntries');
        const timeEntries = timeEntriesContainer.querySelectorAll('.time-entry');

        if (timeEntries.length > 1) {
            event.target.closest('.time-entry').remove();
        } else {
            const entry = event.target.closest('.time-entry');
            entry.querySelector('.entry-time').value = '';
            entry.querySelector('.exit-time').value = '';
        }
    }

    // Function to add new time entry
    function addNewTimeEntry() {
        console.log('Adding new time entry');
        const timeEntriesContainer = document.getElementById('timeEntries');
        if (!timeEntriesContainer) return;

        const template = timeEntriesContainer.querySelector('.time-entry').cloneNode(true);
        template.querySelector('.entry-time').value = '';
        template.querySelector('.exit-time').value = '';

        const removeButton = template.querySelector('.remove-entry');
        removeButton.addEventListener('click', handleRemoveClick);

        timeEntriesContainer.appendChild(template);
    }

    // Initialize all remove buttons
    document.querySelectorAll('.remove-entry').forEach(button => {
        button.addEventListener('click', handleRemoveClick);
    });

    // Add button event listener
    const addButton = document.getElementById('addEntry');
    if (addButton) {
        addButton.addEventListener('click', addNewTimeEntry);
    }

    // Form submission handler
    if (entryForm) {
        entryForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Form submitted');

            const entryType = entryTypeSelect.value;
            let entries = [];

            // Only gather entries if it's a work day
            if (entryType === 'WORK') {
                entries = Array.from(document.querySelectorAll('.time-entry'))
                    .map(entry => ({
                        entry: entry.querySelector('.entry-time').value,
                        exit: entry.querySelector('.exit-time').value
                    }))
                    .filter(entry => entry.entry && entry.exit);
            }

            console.log('Filtered entries:', entries);

            const formData = {
                date: document.getElementById('date').value,
                employee_id: 1, // Default employee
                entries: entries,
                absence_code: entryType === 'WORK' ? null : entryType
            };

            console.log('Sending data:', formData);

            try {
                const response = await fetch('/entry', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const responseData = await response.json();

                if (response.ok) {
                    alert('Entry saved successfully');
                } else {
                    alert(`Error saving entry: ${responseData.error || 'Unknown error'}`);
                }
            } catch (error) {
                alert(`Error saving entry: ${error.message}`);
            }
        });
    }

    // Set initial form state on page load
    toggleWorkDayFields();
});
