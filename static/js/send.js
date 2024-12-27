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
});function deletePost(postId) {
    if (confirm('Czy na pewno chcesz usunąć ten post?')) {
        fetch(`/delete_post/${postId}`, {
            method: 'DELETE',
        })
        .then(response => response.json())
        .then(data => {
            if(data.status === "OK") {
                alert(data.message);
                // Usuń post z DOM
                document.getElementById(`post-${postId}`).remove();
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Wystąpił błąd podczas usuwania posta.');
        });
    }
}

function editPost(postId) {
    const newText = prompt("Wprowadź nową treść posta:");
    if (newText !== null) {
        fetch(`/edit_post/${postId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: newText }),
        })
        .then(response => response.json())
        .then(data => {
            if(data.status === "OK") {
                alert(data.message);
                document.querySelector(`#post-${postId} .post-content`).textContent = newText;
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Wystąpił błąd podczas edycji posta.');
        });
    }
}
