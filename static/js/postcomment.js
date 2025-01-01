document.addEventListener('DOMContentLoaded', function() {
    const commentForms = document.querySelectorAll('.comment-form');
    
    commentForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const postId = this.getAttribute('data-post-id');
            const commentText = this.querySelector('textarea[name="comment-text"]').value;
            
            fetch(`/add_comment/${postId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `comment-text=${encodeURIComponent(commentText)}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === "OK") {
                    const toggleButton = document.querySelector(`.toggle-comments[data-post-id="${postId}"]`);
                    const currentCount = parseInt(toggleButton.textContent.match(/\d+/)[0]);
                    toggleButton.textContent = `Komentarze (${currentCount + 1})`;
                    
                    this.querySelector('textarea[name="comment-text"]').value = '';
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Wystąpił błąd podczas dodawania komentarza.');
            });
        });
    });
});