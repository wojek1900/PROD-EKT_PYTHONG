// Wybieramy wszystkie przyciski z klasą .przycisk_niebieski
buttons = document.querySelectorAll(".przycisk_niebieski");

// Dodajemy zdarzenie kliknięcia dla każdego przycisku
buttons.forEach(button => {
    button.addEventListener('click', function(e) {

        // Obliczamy pozycję kliknięcia względem przycisku
        const rect = e.target.getBoundingClientRect();
        const x = e.clientX - rect.left; // Pozycja pozioma kliknięcia
        const y = e.clientY - rect.top;  // Pozycja pionowa kliknięcia

        // Tworzymy nowy element "span" dla efektu fali
        const ripple = document.createElement("span");
        ripple.classList.add("ripple"); // Dodajemy klasę dla efektu fali
        this.appendChild(ripple); // Dodajemy ripple do przycisku

        // Ustawiamy pozycję fali na miejscu kliknięcia
        ripple.style.left = x + "px";
        ripple.style.top = y + "px";

        // Usuwamy element fali po zakończeniu animacji
        ripple.addEventListener('animationend', () => {
            ripple.remove(); // Usuwamy efekt fali po zakończeniu animacji
        });
    });
});

// Wybieramy wszystkie przyciski rejestracyjne z klasą .register-przycisk_niebieski
buttons_register = document.querySelectorAll(".register-przycisk_niebieski");

// Dodajemy zdarzenie kliknięcia dla każdego przycisku rejestracyjnego
buttons_register.forEach(register_button => {
    register_button.addEventListener('click', function(e) {
        // Obliczamy pozycję kliknięcia względem przycisku
        const rect = e.target.getBoundingClientRect();
        const x = e.clientX - rect.left; // Pozycja pozioma kliknięcia
        const y = e.clientY - rect.top;  // Pozycja pionowa kliknięcia

        // Tworzymy nowy element "span" dla efektu fali
        const ripple = document.createElement("span");
        ripple.classList.add("ripple"); // Dodajemy klasę dla efektu fali
        this.appendChild(ripple); // Dodajemy ripple do przycisku

        // Ustawiamy pozycję fali na miejscu kliknięcia
        ripple.style.left = x + "px";
        ripple.style.top = y + "px";

        // Usuwamy element fali po zakończeniu animacji
        ripple.addEventListener('animationend', () => {
            ripple.remove(); // Usuwamy efekt fali po zakończeniu animacji
        });
    });
});
