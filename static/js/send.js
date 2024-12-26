document.getElementById('post-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    var formData = new FormData(this);
    
    fetch('/public_post', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === "OK") {
            alert(data.message);
            // Tutaj możesz dodać kod do odświeżenia listy postów bez przeładowania strony
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Wystąpił błąd podczas dodawania posta.');
    });
});