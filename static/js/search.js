document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('search-form');
    const radioButtons = searchForm.querySelectorAll('input[type="radio"]');

    radioButtons.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.checked) {
                radioButtons.forEach(otherRadio => {
                    if (otherRadio !== this) {
                        otherRadio.checked = false;
                    }
                });
            }
        });
    });
});