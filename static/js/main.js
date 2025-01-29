function initTypeAnimation() {
    console.log("Załadowano stronę"); 
    const texts = [
        "Antoni Fijałkowski", 
        "Natalia Ostas", 
        "Szymon Fugiel", 
        "Stefan Mickiewicz" 
    ];
    let currentTextIndex = 0; 
    let isAnimating = false; 
    const targetElement = document.getElementById("text"); 
    if (!targetElement) return; 
    targetElement.innerHTML = ""; 

    function isTextAlreadyPresent(text) {
        return targetElement.innerHTML === text;
    }

    function typeText(text, callback) {
        if (isTextAlreadyPresent(text)) {
            callback(); 
            return;
        }

        let index = 0;
        function type() {
            if (index < text.length) {
                targetElement.innerHTML += text.charAt(index); 
                index++;
                setTimeout(type, 100); 
            } else {
                callback(); 
            }
        }
        type(); 
    }

    function deleteText(text, nextText, callback) {
        let content = targetElement.innerHTML;
        let index = content.length;
        function deleteLetter() {
            if (index > 0) {
                if (index === 1) {
                    targetElement.innerHTML = nextText.charAt(0);
                } else {
                    targetElement.innerHTML = content.substring(0, index - 1); 
                }
                index--;
                setTimeout(deleteLetter, 70); 
            } else {
                callback();
            }
        }
        deleteLetter(); 
    }

    function switchText() {
        if (isAnimating) return; 
        isAnimating = true;

        const currentText = texts[currentTextIndex]; 
        const nextText = texts[(currentTextIndex + 1) % texts.length]; 

        typeText(currentText, function() {
            setTimeout(function() {
                deleteText(currentText, nextText, function() {
                    typeText(nextText.substring(1), function() {
                        isAnimating = false; 
                        setTimeout(switchText, 2000); 
                    });
                });
            }, 2000); 
        });
        currentTextIndex = (currentTextIndex + 1) % texts.length; 
    }
    switchText(); 

}

document.addEventListener('DOMContentLoaded', initTypeAnimation);

const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.target.id === 'content') {
            initTypeAnimation(); 
        }
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const contentDiv = document.getElementById('content'); 
    if (contentDiv) {
        observer.observe(contentDiv, {
            childList: true, 
            subtree: true 
        });
    }
});
