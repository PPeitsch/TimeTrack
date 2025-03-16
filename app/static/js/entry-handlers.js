document.addEventListener('DOMContentLoaded', function() {
    console.log('Entry handlers script loaded');

    // Set current date as default
    const dateInput = document.getElementById('date');
    if (dateInput) {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        dateInput.value = `${year}-${month}-${day}`;
    }

    // Function to handle remove button clicks
    function handleRemoveClick(event) {
        console.log('Remove button clicked');
        const timeEntries = document.querySelectorAll('.time-entry');

        // Only remove if there's more than one entry
        if (timeEntries.length > 1) {
            event.target.closest('.time-entry').remove();
        } else {
            // Just clear the values if it's the last one
            const entry = event.target.closest('.time-entry');
            entry.querySelector('.entry-time').value = '';
            entry.querySelector('.exit-time').value = '';
        }
    }

    // Function to add new time entry
    function addNewTimeEntry() {
        console.log('Adding new time entry');
        const timeEntries = document.getElementById('timeEntries');
        const template = document.querySelector('.time-entry').cloneNode(true);

        // Clear the input values
        template.querySelector('.entry-time').value = '';
        template.querySelector('.exit-time').value = '';

        // Add event listener to the new remove button
        const removeButton = template.querySelector('.remove-entry');
        removeButton.addEventListener('click', handleRemoveClick);

        timeEntries.appendChild(template);
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
    const entryForm = document.getElementById('entryForm');
    if (entryForm) {
        entryForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Form submitted');

            // Get all time entries with both values filled
            const entries = Array.from(document.querySelectorAll('.time-entry'))
                .map(entry => ({
                    entry: entry.querySelector('.entry-time').value,
                    exit: entry.querySelector('.exit-time').value
                }))
                .filter(entry => entry.entry && entry.exit);

            console.log('Filtered entries:', entries);

            const entryType = document.getElementById('entryType').value;
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
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });

                const responseData = await response.json();

                if (response.ok) {
                    alert('Entry saved successfully');
                    // Don't reload, just update UI
                    // location.reload();
                } else {
                    alert(`Error saving entry: ${responseData.error || 'Unknown error'}`);
                }
            } catch (error) {
                alert(`Error saving entry: ${error.message}`);
            }
        });
    }
});