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
function addComment(postId) {
    const commentText = document.querySelector(`#comment-input-${postId}`).value;
    if (!commentText) {
        alert('Proszę wpisać treść komentarza.');
        return;
    }

    fetch(`/add_comment/${postId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `comment_text=${encodeURIComponent(commentText)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const commentsContainer = document.querySelector(`#comments-${postId}`);
            const newCommentHtml = `
                <div class="comment">
                    <div class="comment-header">
                        <img src="/static/basics/profile.png" alt="Default profile picture" class="profile-picture">
                        <p class="author-name">${data.comment.author}</p>
                    </div>
                    <p class="comment-content">${data.comment.text}</p>
                </div>
            `;
            commentsContainer.insertAdjacentHTML('beforeend', newCommentHtml);
            document.querySelector(`#comment-input-${postId}`).value = '';
            
            const commentButton = document.querySelector(`button[data-post-id="${postId}"]`);
            const currentCount = parseInt(commentButton.textContent.match(/\d+/)[0]);
            commentButton.textContent = `Komentarze (${currentCount + 1})`;
        } else {
            alert('Wystąpił błąd podczas dodawania komentarza.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Wystąpił błąd podczas dodawania komentarza.');
    });
}
