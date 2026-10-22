// LearnBridge Main JS

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 6000);
    });

    // 2. Filter Reset helper
    const resetBtn = document.getElementById('reset-filters-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = window.location.pathname;
        });
    }

    // 3. Tutor search debounce or auto-submit on change
    const autoFilterSelects = document.querySelectorAll('.auto-submit-filter');
    autoFilterSelects.forEach(select => {
        select.addEventListener('change', () => {
            const form = select.closest('form');
            if (form) form.submit();
        });
    });

    // 4. Modal helper for tuition request
    const requestModal = document.getElementById('tuitionRequestModal');
    if (requestModal) {
        requestModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            if (!button) return;
            const tutorId = button.getAttribute('data-tutor-id');
            const tutorName = button.getAttribute('data-tutor-name');
            const defaultFee = button.getAttribute('data-tutor-fee');

            const modalTitle = requestModal.querySelector('.modal-title');
            const form = requestModal.querySelector('form');
            const budgetInput = requestModal.querySelector('#modal_budget');

            if (modalTitle && tutorName) {
                modalTitle.textContent = `Send Tuition Request to ${tutorName}`;
            }
            if (form && tutorId) {
                form.action = `/tutor/${tutorId}/request`;
            }
            if (budgetInput && defaultFee) {
                budgetInput.value = defaultFee;
            }
        });
    }
});
