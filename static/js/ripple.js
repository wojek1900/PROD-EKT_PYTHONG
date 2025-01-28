buttons = document.querySelectorAll(".przycisk_niebieski");

buttons.forEach(button => {
    button.addEventListener('click', function(e) {

        const rect = e.target.getBoundingClientRect();
        const x = e.clientX - rect.left; 
        const y = e.clientY - rect.top;  

        const ripple = document.createElement("span");
        ripple.classList.add("ripple"); 
        this.appendChild(ripple); 

        ripple.style.left = x + "px";
        ripple.style.top = y + "px";

        ripple.addEventListener('animationend', () => {
            ripple.remove(); 
        });
    });
});

buttons_register = document.querySelectorAll(".register-przycisk_niebieski");

buttons_register.forEach(register_button => {
    register_button.addEventListener('click', function(e) {
        const rect = e.target.getBoundingClientRect();
        const x = e.clientX - rect.left; 
        const y = e.clientY - rect.top;  

        const ripple = document.createElement("span");
        ripple.classList.add("ripple"); 
        this.appendChild(ripple); 

        ripple.style.left = x + "px";
        ripple.style.top = y + "px";

        ripple.addEventListener('animationend', () => {
            ripple.remove(); 
        });
    });
});
