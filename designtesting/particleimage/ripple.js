
document.querySelectorAll(".przycisk_niebieski, .register-przycisk_niebieski").forEach(button => {
    button.addEventListener('click', e => {
        const ripple = document.createElement('span');
        ripple.classList.add('ripple');
        ripple.style.left = `${e.clientX - button.getBoundingClientRect().left}px`;
        ripple.style.top = `${e.clientY - button.getBoundingClientRect().top}px`;
        button.appendChild(ripple);
        setTimeout(() => ripple.remove(), 1000);
    });
});
contentDiv.innerHTML = newContent.innerHTML;
contentDiv.classList.remove('fade-out');
attachListeners();
if (window.initRippleEffect) {
    window.initRippleEffect();
}