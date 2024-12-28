document.addEventListener('DOMContentLoaded', function() {
    const posts = document.querySelectorAll('.post-clickable');

    posts.forEach(post => {
        post.addEventListener('click', function(event) {
            if (!event.target.closest('.reactions') && 
                !event.target.closest('.options-public-post') && 
                !event.target.closest('.comments') &&
                !event.target.closest('.toggle-comments')) {
                const postId = this.dataset.postId;
                window.location.href = "/profile.html";
            }
        });
    });
});