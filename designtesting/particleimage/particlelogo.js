function initparticles() {
    const logo = document.querySelector('.obraz');
    nextParticle = new NextParticle({
        image: logo,
        width: logo.offsetWidth,
        height: logo.offsetHeight,
        particleGap: 2,
        mouseForce: 30,
        noise: 20,
    });
    
    let initialized = false;
    
    function initparticlesx() {
        if (!initialized) {
            nextParticle.stop(); 
            nextParticle.start();
            initialized = true;
        }
    };
    initparticlesx();
}

document.addEventListener('DOMContentLoaded', initparticles);

// Obserwator zmian w elemencie o id 'content'
const observer1 = new MutationObserver((mutations1) => {
    mutations1.forEach((mutation1) => {
        if (mutation1.target.id === 'content') {
            initparticles(); 
        }
    });
});


// Rozpoczynamy obserwację zmian w elemencie o id 'content'
document.addEventListener('DOMContentLoaded', () => {
    const contentDiv = document.getElementById('content'); // Pobieramy element 'content'
    if (contentDiv) {
        observer1.observe(contentDiv, {
            childList: true, // Obserwujemy dodawanie/ usuwanie elementów
            subtree: true // Obserwujemy zmiany w całym drzewie DOM
        });
    }
});





