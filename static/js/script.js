document.addEventListener('DOMContentLoaded', function () {
  function attachLinkListeners() {
      const links = document.querySelectorAll('.nav-link'); 
      links.forEach(link => {
          
          if (!link.hasListener) {
              link.hasListener = true; 
              reloadScripts(scriptsToReload) 
                  .then(() => {
                      console.log('Wszystkie skrypty zostały załadowane poprawnie.');
                  })
                  .catch(error => {
                      console.error('Błąd podczas przeładowywania skryptów:', error);
                  });
              link.addEventListener('click', handleLinkClick); 
          }
      });
  }

  function handleLinkClick(event) {
      event.preventDefault(); 
      const contentDiv = document.getElementById('content'); 
      contentDiv.classList.add('fade-out'); 

      const url = this.getAttribute('href'); 

      history.pushState({ url: url }, '', url);

      setTimeout(() => {
          fetch(url)
              .then(response => {
                  if (!response.ok) throw new Error('Błąd odpowiedzi sieciowej');
                  return response.text();
              })
              .then(data => {
                  const parser = new DOMParser();
                  const htmlDoc = parser.parseFromString(data, 'text/html');
                  const newContent = htmlDoc.getElementById('content');
                  contentDiv.innerHTML = newContent.innerHTML;
                  contentDiv.classList.remove('fade-out');

                  attachLinkListeners();

                  executeScriptsIn(newContent);
              })
              .catch(error => {
                  console.error('Błąd pobierania:', error);
                  contentDiv.classList.remove('fade-out'); 
              });
      }, 500);
  }

  function executeScriptsIn(element) {
      const scripts = Array.from(element.querySelectorAll('script'));
      scripts.forEach(script => {
          const newScript = document.createElement('script');
          if (script.src) {
              newScript.src = script.src;
          } else {
              newScript.textContent = script.textContent; 
          }
          
          document.body.appendChild(newScript);
      });
  }

  window.addEventListener('popstate', function (event) {
      const contentDiv = document.getElementById('content');
      const currentUrl = window.location.href; 

      contentDiv.classList.add('fade-out'); 

      setTimeout(() => {
          fetch(currentUrl)
              .then(response => {
                  if (!response.ok) throw new Error('Błąd odpowiedzi sieciowej');
                  return response.text();
              })
              .then(data => {
                  const parser = new DOMParser();
                  const htmlDoc = parser.parseFromString(data, 'text/html');
                  const newContent = htmlDoc.getElementById('content');
                  contentDiv.innerHTML = newContent.innerHTML;
                  contentDiv.classList.remove('fade-out'); 

                  attachLinkListeners();
                  executeScriptsIn(newContent);
              })
              .catch(error => {
                  console.error('Błąd pobierania:', error);
                  contentDiv.classList.remove('fade-out');
              });
      }, 500); 
  });

  attachLinkListeners();
});

function removeScript(src) {
  const scripts = document.querySelectorAll(`script[src="${src}"]`); 
  scripts.forEach(script => script.remove()); 
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src + '?v=' + Date.now(); 
      script.onload = resolve; 
      script.onerror = reject; 
      document.head.appendChild(script); 
  });
}

function reloadScripts(scriptsArray) {
  return scriptsArray.reduce((promiseChain, src) => {
      return promiseChain.then(() => {
          removeScript(src); 
          return loadScript(src); 
      });
  }, Promise.resolve());
}

const scriptsToReload = [
  'main.js',
  'ripple.js'
];
