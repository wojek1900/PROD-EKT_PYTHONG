document.getElementById('load-page1').addEventListener('click', () => loadContent('page1.html'));
document.getElementById('load-page2').addEventListener('click', () => loadContent('page2.html'));

function loadContent(url) {
    const content = document.getElementById('content');

    // Fade out
    content.classList.add('hidden');

    // Wait for the fade-out effect
    setTimeout(() => {
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Błąd sieci!');
                }
                return response.text();
            })
            .then(html => {
                // Update content and fade in
                content.innerHTML = html;
                content.classList.remove('hidden');
            })
            .catch(error => {
                content.innerHTML = `<p style="color: red;">${error.message}</p>`;
                content.classList.remove('hidden');
            });
    }, 500); // Match the duration of the fade-out effect
}
