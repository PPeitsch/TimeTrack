document.addEventListener('DOMContentLoaded', function () {
    const addCodeForm = document.getElementById('addCodeForm');
    const newCodeInput = document.getElementById('newCodeInput');
    const codesTableBody = document.getElementById('codesTableBody');
    const loadingIndicator = document.getElementById('loadingIndicator');

    // Modal elements
    const editCodeModalEl = document.getElementById('editCodeModal');
    const editCodeModal = new bootstrap.Modal(editCodeModalEl);
    const editCodeIdInput = document.getElementById('editCodeId');
    const editCodeInput = document.getElementById('editCodeInput');
    const saveEditBtn = document.getElementById('saveEditBtn');

    const API_URL = '/settings/api/absence-codes';

    // --- Core Functions ---

    async function fetchCodes() {
        loadingIndicator.style.display = 'block';
        codesTableBody.innerHTML = '';
        try {
            const response = await fetch(API_URL);
            if (!response.ok) throw new Error('Failed to fetch codes');
            const codes = await response.json();
            renderCodes(codes);
        } catch (error) {
            console.error(error);
            codesTableBody.innerHTML = `<tr><td colspan="2" class="text-center text-danger">Error loading codes.</td></tr>`;
        } finally {
            loadingIndicator.style.display = 'none';
        }
    }

    function renderCodes(codes) {
        codesTableBody.innerHTML = '';
        if (codes.length === 0) {
            codesTableBody.innerHTML = `<tr><td colspan="2" class="text-center">No absence codes found.</td></tr>`;
            return;
        }
        codes.forEach(code => {
            const row = document.createElement('tr');
            row.dataset.id = code.id;
            row.innerHTML = `
                <td>${escapeHTML(code.code)}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary edit-btn" data-id="${code.id}" data-code="${escapeHTML(code.code)}">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${code.id}">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </td>
            `;
            codesTableBody.appendChild(row);
        });
    }

    // --- Event Handlers ---

    addCodeForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const code = newCodeInput.value.trim();
        if (!code) return;

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Failed to add code');

            newCodeInput.value = '';
            await fetchCodes(); // Refresh the list
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    });

    codesTableBody.addEventListener('click', function (e) {
        const target = e.target.closest('button');
        if (!target) return;

        const id = target.dataset.id;
        if (target.classList.contains('edit-btn')) {
            const code = target.dataset.code;
            editCodeIdInput.value = id;
            editCodeInput.value = code;
            editCodeModal.show();
        } else if (target.classList.contains('delete-btn')) {
            if (confirm('Are you sure you want to delete this code? This action cannot be undone.')) {
                deleteCode(id);
            }
        }
    });

    saveEditBtn.addEventListener('click', async function () {
        const id = editCodeIdInput.value;
        const code = editCodeInput.value.trim();
        if (!id || !code) return;

        try {
            const response = await fetch(`${API_URL}/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Failed to update code');

            editCodeModal.hide();
            await fetchCodes(); // Refresh the list
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    });

    async function deleteCode(id) {
        try {
            const response = await fetch(`${API_URL}/${id}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Failed to delete code');

            await fetchCodes(); // Refresh the list
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }

    // --- Utility ---
    function escapeHTML(str) {
        return str.replace(/[&<>"']/g, function(match) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }[match];
        });
    }

    // --- Initial Load ---
    fetchCodes();
});
