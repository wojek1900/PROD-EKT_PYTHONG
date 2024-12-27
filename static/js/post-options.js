document.addEventListener('DOMContentLoaded', function() {
    const posts = document.querySelectorAll('.post');

    posts.forEach(post => {
        const authorId = post.dataset.authorId;
        const optionsDiv = post.querySelector('.options-public-post');

        if (authorId === currentUserId) {
            post.addEventListener('mouseenter', () => {
                optionsDiv.style.display = 'block';
            });

            post.addEventListener('mouseleave', () => {
                optionsDiv.style.display = 'none';
            });
        }
    });
});
