function initTypeAnimation() {
    console.log("Załadowano stronę"); // Informacja o załadowaniu strony
    const texts = [
        "Wild Snakes Messagging approch", // Tekst 1
        "Dzikie węże : SnakeLine", // Tekst 2
        "Antoni Fijałkowski", // Tekst 3
        "Natalia Ostas", // Tekst 4
        "Szymon Fugiel", // Tekst 5
        "Stefan Mickiewicz" // Tekst 6
    ];
    let currentTextIndex = 0; // Indeks aktualnie wyświetlanego tekstu
    let isAnimating = false; // Flaga określająca, czy animacja jest w toku
    const targetElement = document.getElementById("text"); // Element, w którym wyświetlany jest tekst
    if (!targetElement) return; // Jeśli element nie istnieje, kończymy działanie funkcji
    targetElement.innerHTML = ""; // Czyścimy zawartość elementu przed rozpoczęciem animacji

    // Funkcja sprawdzająca, czy tekst jest już obecny
    function isTextAlreadyPresent(text) {
        return targetElement.innerHTML === text;
    }

    // Funkcja do wpisywania tekstu
    function typeText(text, callback) {
        if (isTextAlreadyPresent(text)) {
            callback(); // Jeśli tekst już jest, uruchamiamy callback
            return;
        }

        let index = 0;
        function type() {
            if (index < text.length) {
                targetElement.innerHTML += text.charAt(index); // Dodajemy kolejny znak do wyświetlania
                index++;
                setTimeout(type, 100); // Czekamy 100ms przed dodaniem kolejnego znaku
            } else {
                callback(); // Po zakończeniu wpisywania, wywołujemy callback
            }
        }
        type(); // Rozpoczynamy wpisywanie tekstu
    }

    // Funkcja do usuwania tekstu
    function deleteText(text, nextText, callback) {
        let content = targetElement.innerHTML;
        let index = content.length;
        function deleteLetter() {
            if (index > 0) {
                if (index === 1) {
                    targetElement.innerHTML = nextText.charAt(0); // Usuwamy tekst, a potem ustawiamy pierwszy znak nowego tekstu
                } else {
                    targetElement.innerHTML = content.substring(0, index - 1); // Usuwamy jeden znak
                }
                index--;
                setTimeout(deleteLetter, 70); // Czekamy 70ms przed usunięciem kolejnego znaku
            } else {
                callback(); // Po usunięciu tekstu, uruchamiamy callback
            }
        }
        deleteLetter(); // Rozpoczynamy usuwanie tekstu
    }

    // Funkcja do przełączania tekstów
    function switchText() {
        if (isAnimating) return; // Jeśli animacja już trwa, nie zaczynaj nowej
        isAnimating = true;

        const currentText = texts[currentTextIndex]; // Aktualny tekst
        const nextText = texts[(currentTextIndex + 1) % texts.length]; // Następny tekst (cyklicznie)

        // Typowanie tekstu
        typeText(currentText, function() {
            setTimeout(function() {
                // Usuwanie aktualnego tekstu
                deleteText(currentText, nextText, function() {
                    // Typowanie nowego tekstu
                    typeText(nextText.substring(1), function() {
                        isAnimating = false; // Kończymy animację
                        setTimeout(switchText, 2000); // Czekamy 2 sekundy przed rozpoczęciem następnej animacji
                    });
                });
            }, 2000); // Czekamy 2 sekundy po zakończeniu typowania
        });
        currentTextIndex = (currentTextIndex + 1) % texts.length; // Zmieniamy indeks tekstu (cyklicznie)
    }
    switchText(); // Rozpoczynamy animację
}

// Inicjalizacja animacji po załadowaniu strony
document.addEventListener('DOMContentLoaded', initTypeAnimation);

// Obserwator zmian w elemencie o id 'content'
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.target.id === 'content') {
            initTypeAnimation(); // Jeśli zawartość 'content' się zmieni, uruchamiamy animację
        }
    });
});

// Rozpoczynamy obserwację zmian w elemencie o id 'content'
document.addEventListener('DOMContentLoaded', () => {
    const contentDiv = document.getElementById('content'); // Pobieramy element 'content'
    if (contentDiv) {
        observer.observe(contentDiv, {
            childList: true, // Obserwujemy dodawanie/ usuwanie elementów
            subtree: true // Obserwujemy zmiany w całym drzewie DOM
        });
    }
});



