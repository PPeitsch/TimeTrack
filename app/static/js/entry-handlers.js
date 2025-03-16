document.addEventListener('DOMContentLoaded', function() {
    // Add button functionality
    document.getElementById('addEntry').addEventListener('click', function() {
        const template = document.querySelector('.time-entry').cloneNode(true);
        template.querySelector('.entry-time').value = '';
        template.querySelector('.exit-time').value = '';

        // Add event listener to the new remove button
        const removeButton = template.querySelector('.remove-entry');
        if (removeButton) {
            removeButton.addEventListener('click', removeTimeEntry);
        }

        document.getElementById('timeEntries').appendChild(template);
    });

    // Setup initial remove buttons
    document.querySelectorAll('.remove-entry').forEach(button => {
        button.addEventListener('click', removeTimeEntry);
    });

    // Function to handle remove button clicks
    function removeTimeEntry() {
        const timeEntries = document.querySelectorAll('.time-entry');
        // Only remove if there's more than one entry
        if (timeEntries.length > 1) {
            this.closest('.time-entry').remove();
        } else {
            // Just clear the values if it's the last one
            const entry = this.closest('.time-entry');
            entry.querySelector('.entry-time').value = '';
            entry.querySelector('.exit-time').value = '';
        }
    }

    // Handle form submission
    document.getElementById('entryForm').addEventListener('submit', async function(e) {
        e.preventDefault();

        // Get all time entries and filter out incomplete ones
        const entries = Array.from(document.querySelectorAll('.time-entry'))
            .map(entry => ({
                entry: entry.querySelector('.entry-time').value,
                exit: entry.querySelector('.exit-time').value
            }))
            .filter(entry => entry.entry && entry.exit); // Only include complete entries

        // Get absence code (if not "Work Day")
        const entryType = document.getElementById('entryType').value;
        const absenceCode = entryType === 'WORK' ? null : entryType;

        const formData = {
            date: document.getElementById('date').value,
            employee_id: 1, // Default employee
            entries: entries,
            absence_code: absenceCode
        };

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
                location.reload();
            } else {
                alert(`Error saving entry: ${responseData.error || 'Unknown error'}`);
            }
        } catch (error) {
            alert(`Error saving entry: ${error.message}`);
        }
    });
});