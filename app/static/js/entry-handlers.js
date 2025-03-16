document.addEventListener('DOMContentLoaded', function() {
    // Add button functionality
    document.getElementById('addEntry').addEventListener('click', function() {
        const template = document.querySelector('.time-entry').cloneNode(true);
        template.querySelector('.entry-time').value = '';
        template.querySelector('.exit-time').value = '';

        // Add event listener to the new remove button
        setupRemoveButtonListener(template.querySelector('.remove-entry'));

        document.getElementById('timeEntries').appendChild(template);
    });

    // Setup initial remove buttons
    document.querySelectorAll('.remove-entry').forEach(button => {
        setupRemoveButtonListener(button);
    });

    function setupRemoveButtonListener(button) {
        button.addEventListener('click', function() {
            // Get the parent time-entry element
            const timeEntry = this.closest('.time-entry');

            // If there's more than one time entry, remove this one
            if (document.querySelectorAll('.time-entry').length > 1) {
                timeEntry.remove();
            } else {
                // If it's the last one, just clear the values
                timeEntry.querySelector('.entry-time').value = '';
                timeEntry.querySelector('.exit-time').value = '';
            }
        });
    }

    // Handle form submission
    document.getElementById('entryForm').addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = {
            date: document.getElementById('date').value,
            employee_id: 1, // Temporal hasta implementar login
            entries: Array.from(document.querySelectorAll('.time-entry')).map(entry => ({
                entry: entry.querySelector('.entry-time').value,
                exit: entry.querySelector('.exit-time').value
            })).filter(entry => entry.entry && entry.exit), // Only include entries with both times filled
            absence_code: document.getElementById('entryType').value === 'WORK' ? null : document.getElementById('entryType').value
        };

        try {
            const response = await fetch('/entry', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                alert('Entry saved successfully');
                location.reload();
            } else {
                const errorData = await response.json();
                alert(`Error saving entry: ${errorData.error || 'Unknown error'}`);
            }
        } catch (error) {
            alert(`Error saving entry: ${error.message}`);
        }
    });
});