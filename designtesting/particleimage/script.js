document.addEventListener('DOMContentLoaded', function () {
  // Funkcja dodająca event listenery do linków
  function attachLinkListeners() {
      const links = document.querySelectorAll('.nav-link'); // Wybieramy wszystkie linki z klasą .nav-link
      links.forEach(link => {
          // Sprawdzamy czy link już nie ma listenera, aby uniknąć dodawania tego samego listenera wielokrotnie
          if (!link.hasListener) {
              link.hasListener = true; // Ustawiamy flagę, że listener został dodany
              reloadScripts(scriptsToReload) // Ładujemy i reloadujemy skrypty
                  .then(() => {
                      console.log('Wszystkie skrypty zostały załadowane poprawnie.');
                  })
                  .catch(error => {
                      console.error('Błąd podczas przeładowywania skryptów:', error);
                  });
              link.addEventListener('click', handleLinkClick); // Dodajemy listener na kliknięcie w link
          }
      });
  }

  // Funkcja obsługująca kliknięcie w link
  function handleLinkClick(event) {
      event.preventDefault(); // Zatrzymujemy domyślne działanie linku (czyli przeładowanie strony)
      const contentDiv = document.getElementById('content'); // Pobieramy element, w którym jest zawartość
      contentDiv.classList.add('fade-out'); // Dodajemy klasę, która animuje znikanie zawartości

      const url = this.getAttribute('href'); // Pobieramy adres URL z linku

      // Dodajemy nowy stan do historii przeglądarki
      history.pushState({ url: url }, '', url);

      setTimeout(() => {
          // Pobieramy nową stronę przez fetch
          fetch(url)
              .then(response => {
                  if (!response.ok) throw new Error('Błąd odpowiedzi sieciowej');
                  return response.text();
              })
              .then(data => {
                  // Parsujemy pobraną stronę i wyciągamy nową zawartość
                  const parser = new DOMParser();
                  const htmlDoc = parser.parseFromString(data, 'text/html');
                  const newContent = htmlDoc.getElementById('content');
                  contentDiv.innerHTML = newContent.innerHTML; // Aktualizujemy zawartość
                  contentDiv.classList.remove('fade-out'); // Usuwamy klasę, aby zakończyć animację

                  // Ponownie dodajemy event listenery do nowych linków
                  attachLinkListeners();

                  // Wykonujemy skrypty w nowej zawartości
                  executeScriptsIn(newContent);
              })
              .catch(error => {
                  console.error('Błąd pobierania:', error);
                  contentDiv.classList.remove('fade-out'); // W razie błędu, usuwamy animację
              });
      }, 500); // Opóźnienie przed rozpoczęciem ładowania nowej zawartości
  }

  // Funkcja do wykonywania skryptów wewnątrz konkretnego elementu
  function executeScriptsIn(element) {
      const scripts = Array.from(element.querySelectorAll('script')); // Pobieramy wszystkie skrypty w nowej zawartości
      scripts.forEach(script => {
          // Tworzymy nowy tag <script>
          const newScript = document.createElement('script');
          // Ustawiamy źródło skryptu
          if (script.src) {
              newScript.src = script.src;
          } else {
              newScript.textContent = script.textContent; // W przypadku skryptu inline, ustawiamy jego kod
          }
          // Dodajemy nowy skrypt do dokumentu
          document.body.appendChild(newScript);
      });
  }

  // Obsługuje zdarzenie 'popstate' (dla nawigacji wstecz/naprzód)
  window.addEventListener('popstate', function (event) {
      const contentDiv = document.getElementById('content');
      const currentUrl = window.location.href; // Pobieramy aktualny URL

      contentDiv.classList.add('fade-out'); // Dodajemy animację znikania zawartości

      setTimeout(() => {
          // Ładujemy stronę przy pomocy fetch, tak jak przy kliknięciu w link
          fetch(currentUrl)
              .then(response => {
                  if (!response.ok) throw new Error('Błąd odpowiedzi sieciowej');
                  return response.text();
              })
              .then(data => {
                  // Parsujemy odpowiedź i aktualizujemy zawartość
                  const parser = new DOMParser();
                  const htmlDoc = parser.parseFromString(data, 'text/html');
                  const newContent = htmlDoc.getElementById('content');
                  contentDiv.innerHTML = newContent.innerHTML;
                  contentDiv.classList.remove('fade-out'); // Kończymy animację

                  // Ponownie dodajemy event listenery i wykonujemy skrypty
                  attachLinkListeners();
                  executeScriptsIn(newContent);
              })
              .catch(error => {
                  console.error('Błąd pobierania:', error);
                  contentDiv.classList.remove('fade-out');
              });
      }, 500); // Opóźnienie przed rozpoczęciem ładowania zawartości
  });

  // Pierwsze dodanie listenerów do linków po załadowaniu strony
  attachLinkListeners();
});

// Funkcja do usuwania skryptów w pamięci po tagach <script>
function removeScript(src) {
  const scripts = document.querySelectorAll(`script[src="${src}"]`); // Wyszukujemy skrypty o danym src
  scripts.forEach(script => script.remove()); // Usuwamy je
}

// Funkcja do załadowania skryptu
function loadScript(src) {
  return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src + '?v=' + Date.now(); // Dodajemy parametr wersji, żeby wymusić ponowne pobranie
      script.onload = resolve; // Skrypt załadowany pomyślnie
      script.onerror = reject; // Błąd ładowania skryptu
      document.head.appendChild(script); // Dodajemy skrypt do dokumentu
  });
}

// Funkcja do przeładowania skryptów w zadanej kolejności
function reloadScripts(scriptsArray) {
  return scriptsArray.reduce((promiseChain, src) => {
      return promiseChain.then(() => {
          removeScript(src); // Usuwamy poprzedni skrypt
          return loadScript(src); // Ładujemy nowy skrypt
      });
  }, Promise.resolve());
}

// Lista skryptów do przeładowania
const scriptsToReload = [
    'main.js',
    'ripple.js',
    "https://nextparticle.nextco.de/nextparticle.min.js",
    "particlelogo.js"
];
