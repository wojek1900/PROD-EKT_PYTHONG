document.addEventListener('DOMContentLoaded', function() {
    const toggleButtons = document.querySelectorAll('.toggle-comments');

    toggleButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.stopPropagation();
            const postId = this.dataset.postId;
            const commentsDiv = document.getElementById(`comments-${postId}`);

            if (commentsDiv.style.display === 'none') {
                commentsDiv.style.display = 'block';
                this.textContent = `Ukryj komentarze (${commentsDiv.querySelectorAll('.comment').length})`;
            } else {
                commentsDiv.style.display = 'none';
                this.textContent = `Komentarze (${commentsDiv.querySelectorAll('.comment').length})`;
            }
        });
    });
});