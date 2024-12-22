function initparticles1() {
    const logo1 = document.querySelector('.register-obraz1');
    nextParticle1 = new NextParticle({
        image: logo1,
        width: logo1.offsetWidth,
        height: logo1.offsetHeight,
        particleGap: 3,
        mouseForce: 25,
        noise: 20,
    });
    
    let initialized1 = false;

    function initparticlesx1() {
        if (!initialized1) {
            smoothReload();
            nextParticle1.start();
            initialized1 = true;
        }
    };
    initparticlesx1();
    
}
document.addEventListener('DOMContentLoaded', initparticles1);

// Obserwator zmian w elemencie o id 'content'
const observer2 = new MutationObserver((mutations2) => {
    mutations2.forEach((mutation2) => {
        if (mutation2.target.id === 'content') {
            initparticles1(); 
        }
    });
});


// Rozpoczynamy obserwację zmian w elemencie o id 'content'
document.addEventListener('DOMContentLoaded', () => {
    const contentDiv = document.getElementById('content'); // Pobieramy element 'content'
    if (contentDiv) {
        observer2.observe(contentDiv, {
            childList: true, // Obserwujemy dodawanie/ usuwanie elementów
            subtree: true // Obserwujemy zmiany w całym drzewie DOM
        });
    }
});