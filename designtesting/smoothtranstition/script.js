document.addEventListener('DOMContentLoaded', function() {
    initializeAjaxNavigation();
    setupInitialAnimation();
});

function initializeAjaxNavigation() {
    document.body.addEventListener('click', function(e) {
        if (e.target.classList.contains('ajax-link')) {
            e.preventDefault();
            let url = e.target.getAttribute('href');
            navigateTo(url);
        }
    });

    window.addEventListener('popstate', function(e) {
        if (e.state && e.state.url) {
            loadContent(e.state.url, false);
        }
    });
}

function setupInitialAnimation() {
    let intro = document.querySelector('.intro');
    let main = document.querySelector('main');

    // ukryj intro
    setTimeout(() => {
        intro.style.opacity = '0';
        intro.style.visibility = 'hidden';
    }, 3000); // dostosuj czas do zależności od czasu wykonania CSS animacji
}

function navigateTo(url) {
    history.pushState({ url: url }, '', url);
    loadContent(url, true);
}

function loadContent(url, updateHistory) {
    fetch(url)
        .then(response => response.text())
        .then(html => {
            let parser = new DOMParser();
            let doc = parser.parseFromString(html, 'text/html');
            let newContent = doc.getElementById('content');
            let currentContent = document.getElementById('content');

            currentContent.style.opacity = 0;
            setTimeout(() => {
                document.title = doc.title;
                currentContent.innerHTML = newContent.innerHTML;
                currentContent.style.opacity = 1;
                if (updateHistory) {
                    initializeAjaxNavigation();
                }
                // Zresetuj animacje gdy zaktualizowano treść
                resetAnimations();
            }, 500);
        })
        .catch(error => console.error('Error:', error));
}

function resetAnimations() {
    let main = document.querySelector('main');
    let h2 = document.querySelector('main h2');
    let p = document.querySelector('main p');

    main.style.animation = 'none';
    if (h2) h2.style.animation = 'none';
    if (p) p.style.animation = 'none';

    void main.offsetWidth; // ponów reflow
    if (h2) void h2.offsetWidth;
    if (p) void p.offsetWidth;

    main.style.animation = null;
    if (h2) h2.style.animation = null;
    if (p) p.style.animation = null;

    // ukryj intro
    let intro = document.querySelector('.intro');
    intro.style.opacity = '0';
    intro.style.visibility = 'hidden';
}