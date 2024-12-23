let nextParticle1;

async function clearCanvasMemory() {
    if (nextParticle1) {
        nextParticle1.stop();
        nextParticle1 = null;
    }
    if (nextParticle) {
        nextParticle.stop();
        nextParticle = null;
    }
}

async function initparticles1() {
    await clearCanvasMemory();

    const logo1 = document.querySelector('.register-obraz1');
    if (!logo1) {
        console.log('Element .register-obraz1 nie został znaleziony');
        return;
    }

    nextParticle1 = new NextParticle({
        image: logo1,
        width: logo1.offsetWidth,
        height: logo1.offsetHeight,
        particleGap: 3,
        mouseForce: 25,
        noise: 20,
    });

    await new Promise(resolve => setTimeout(resolve, 0)); // Mikro-opóźnienie dla lepszej wydajności

    smoothReload();
    nextParticle1.start();
}

async function initAllAnimations() {
    await clearCanvasMemory();
    await initparticles1();
    // Tutaj możesz dodać inicjalizację innych animacji canvas
}

document.addEventListener('DOMContentLoaded', initAllAnimations);

// Obserwator zmian w elemencie o id 'content'
const observer2 = new MutationObserver((mutations2) => {
    mutations2.forEach((mutation2) => {
        const current_link = document.URL;
        if (mutation2.target.id === 'content' && (current_link.includes('register') || current_link.includes('login'))) {
            initAllAnimations();
        }
    });
});

// Rozpoczynamy obserwację zmian w elemencie o id 'content'
document.addEventListener('DOMContentLoaded', () => {
    const contentDiv = document.getElementById('content');
    if (contentDiv) {
        observer2.observe(contentDiv, {
            childList: true,
            subtree: true
        });
    }
});

// Funkcja do płynnego przeładowania (jeśli jest potrzebna)
function smoothReload() {
    // Implementacja smoothReload, jeśli jest wymagana
}