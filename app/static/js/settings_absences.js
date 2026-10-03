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
        loadingIndicator.hidden = false;
        codesTableBody.innerHTML = '';
        try {
            const response = await fetch(API_URL);
            if (!response.ok) throw new Error(t('load_codes_error'));
            const codes = await response.json();
            renderCodes(codes);
        } catch (error) {
            console.error(error);
            codesTableBody.innerHTML = `<tr><td colspan="2" class="text-center text-danger">${escapeHTML(t('load_codes_error'))}</td></tr>`;
        } finally {
            loadingIndicator.hidden = true;
        }
    }

    function renderCodes(codes) {
        codesTableBody.innerHTML = '';
        if (codes.length === 0) {
            codesTableBody.innerHTML = `<tr><td colspan="2" class="text-center text-body-secondary">${escapeHTML(t('no_codes'))}</td></tr>`;
            return;
        }
        codes.forEach(code => {
            const row = document.createElement('tr');
            row.dataset.id = code.id;
            row.innerHTML = `
                <td>${escapeHTML(code.code)}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary edit-btn" data-id="${code.id}" data-code="${escapeHTML(code.code)}">
                        ${icon('pencil')} ${escapeHTML(t('edit'))}
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${code.id}">
                        ${icon('trash')} ${escapeHTML(t('delete'))}
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
            if (!response.ok) throw new Error(result.error || t('add_code_error'));

            newCodeInput.value = '';
            showToast(t('code_added'));
            await fetchCodes(); // Refresh the list
        } catch (error) {
            showToast(error.message, 'error');
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
            if (confirm(t('confirm_delete'))) {
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
            if (!response.ok) throw new Error(result.error || t('update_code_error'));
            showToast(t('code_updated'));

            editCodeModal.hide();
            await fetchCodes(); // Refresh the list
        } catch (error) {
            showToast(error.message, 'error');
        }
    });

    async function deleteCode(id) {
        try {
            const response = await fetch(`${API_URL}/${id}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || t('delete_code_error'));
            showToast(t('code_deleted'));

            await fetchCodes(); // Refresh the list
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    // --- Initial Load ---
    fetchCodes();
});
