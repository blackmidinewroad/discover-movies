document.addEventListener('DOMContentLoaded', function () {
    const checkboxes = document.querySelectorAll('.mutually-exclusive');

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            if (this.checked) {
                const group = this.getAttribute('data-group');
                document.querySelectorAll(`.mutually-exclusive[data-group="${group}"]`).forEach(otherCheckbox => {
                    if (otherCheckbox !== this) {
                        otherCheckbox.checked = false;
                    }
                });
            }
        });
    });
});