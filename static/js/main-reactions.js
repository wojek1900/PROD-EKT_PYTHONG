document.addEventListener('DOMContentLoaded', function() {
    const reactionButtons = document.querySelectorAll('.reaction-btn');

    reactionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const postId = this.dataset.postId;
            const reactionType = this.dataset.reactionType;

            fetch(`/add_reaction/${postId}/${reactionType}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                updateReactionCounts(postId);
            });
        });
    });

    function updateReactionCounts(postId) {
        fetch(`/get_reactions/${postId}`)
        .then(response => response.json())
        .then(data => {
            for (const [reactionType, count] of Object.entries(data)) {
                const countElement = document.getElementById(`count-${postId}-${reactionType}`);
                if (countElement) {
                    countElement.textContent = count;
                }
            }
        });
    }

    document.querySelectorAll('.post').forEach(post => {
        const postId = post.querySelector('.reaction-btn').dataset.postId;
        updateReactionCounts(postId);
    });
});