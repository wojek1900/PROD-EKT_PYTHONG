document.addEventListener('DOMContentLoaded', function() {
    const posts = document.getElementById('posts');
    const editForm = document.getElementById('editForm');
    const overlay = document.getElementById('overlay');
    const editContent = document.getElementById('editContent');
    const saveEdit = document.getElementById('saveEdit');
    const cancelEdit = document.getElementById('cancelEdit');
    const existingAttachments = document.getElementById('existingAttachments');
    const editFiles = document.getElementById('editFiles');
    let currentPostId = null;
    let currentAttachments = [];

    const filesInput = document.getElementById('files');
    const attachmentsPreview = document.getElementById('attachments-preview');

    filesInput.addEventListener('change', function(e) {
        attachmentsPreview.innerHTML = '';
        for (let file of e.target.files) {
            const attachmentDiv = createAttachmentPreview(file);
            attachmentsPreview.appendChild(attachmentDiv);
        }
    });

    function createAttachmentPreview(file) {
        const attachmentDiv = document.createElement('div');
        attachmentDiv.className = 'attachment-preview';
        attachmentDiv.style.width = '100px';
        attachmentDiv.style.height = '100px';
        attachmentDiv.style.backgroundColor = 'white';
        attachmentDiv.style.position = 'relative';
        attachmentDiv.style.display = 'inline-block';
        attachmentDiv.style.margin = '5px';

        const removeButton = document.createElement('button');
        removeButton.textContent = 'x';
        removeButton.style.position = 'absolute';
        removeButton.style.top = '0';
        removeButton.style.right = '0';
        removeButton.addEventListener('click', () => {
            attachmentDiv.remove();
            const dt = new DataTransfer();
            const { files } = filesInput;
            for (let i = 0; i < files.length; i++) {
                if (files[i] !== file) {
                    dt.items.add(files[i]);
                }
            }
            filesInput.files = dt.files;
        });

        if (file.type.startsWith('image/')) {
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'cover';
            attachmentDiv.appendChild(img);
        } else if (file.type.startsWith('video/')) {
            const icon = document.createElement('div');
            icon.textContent = '🎥';
            icon.style.fontSize = '40px';
            icon.style.textAlign = 'center';
            icon.style.lineHeight = '100px';
            attachmentDiv.appendChild(icon);
        } else if (file.type.startsWith('audio/')) {
            const icon = document.createElement('div');
            icon.textContent = '🎵';
            icon.style.fontSize = '40px';
            icon.style.textAlign = 'center';
            icon.style.lineHeight = '100px';
            attachmentDiv.appendChild(icon);
        } else {
            const icon = document.createElement('div');
            icon.textContent = '📎';
            icon.style.fontSize = '40px';
            icon.style.textAlign = 'center';
            icon.style.lineHeight = '100px';
            attachmentDiv.appendChild(icon);
        }

        attachmentDiv.appendChild(removeButton);
        return attachmentDiv;
    }

    posts.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-post')) {
            const postId = e.target.dataset.postId;
            if (confirm('Czy na pewno chcesz usunąć ten post?')) {
                fetch(`/delete_post/${postId}`, {
                    method: 'POST',
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === "OK") {
                        const postElement = e.target.closest('.post');
                        postElement.remove();
                        alert(data.message);
                    } else {
                        alert(`Błąd: ${data.message}`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert(`Wystąpił błąd podczas usuwania posta: ${error.message}`);
                });
            }
        } else if (e.target.classList.contains('edit-post')) {
            const postElement = e.target.closest('.post');
            currentPostId = e.target.dataset.postId;
            const contentElement = postElement.querySelector('.post-content');
            editContent.value = contentElement.textContent;
            
            existingAttachments.innerHTML = '';
            currentAttachments = [];

            const attachments = postElement.querySelectorAll('.attachments img, .attachments video, .attachments audio, .attachments a');
            attachments.forEach((attachment, index) => {
                const attachmentDiv = document.createElement('div');
                attachmentDiv.className = 'attachment-preview';
                attachmentDiv.style.width = '100px';
                attachmentDiv.style.height = '100px';
                attachmentDiv.style.backgroundColor = 'white';
                attachmentDiv.style.position = 'relative';
                attachmentDiv.style.display = 'inline-block';
                attachmentDiv.style.margin = '5px';

                const removeButton = document.createElement('button');
                removeButton.textContent = `x`;
                removeButton.style.position = 'absolute';
                removeButton.style.top = '0';
                removeButton.style.right = '0';
                removeButton.addEventListener('click', () => {
                    attachmentDiv.remove();
                    currentAttachments = currentAttachments.filter(a => a.id !== attachment.dataset.id);
                });
                if (attachment.tagName === 'IMG') {
                    const img = document.createElement('img');
                    img.src = attachment.src;
                    img.style.width = '100%';
                    img.style.height = '100%';
                    img.style.objectFit = 'cover';
                    attachmentDiv.appendChild(img);
                } else if (attachment.tagName === 'VIDEO' || attachment.tagName === 'AUDIO') {
                    const icon = document.createElement('div');
                    icon.textContent = attachment.tagName === 'VIDEO' ? '🎥' : '🎵';
                    icon.style.fontSize = '40px';
                    icon.style.textAlign = 'center';
                    icon.style.lineHeight = '100px';
                    attachmentDiv.appendChild(icon);
                } else {
                    const icon = document.createElement('div');
                    icon.textContent = '📎';
                    icon.style.fontSize = '40px';
                    icon.style.textAlign = 'center';
                    icon.style.lineHeight = '100px';
                    attachmentDiv.appendChild(icon);
                }
                attachmentDiv.appendChild(removeButton);
                existingAttachments.appendChild(attachmentDiv);

                currentAttachments.push({
                    id: attachment.dataset.id,
                    name: attachment.alt || attachment.textContent
                });
            });
            editForm.style.display = 'block';
            overlay.style.display = 'block';
        }
    });

    saveEdit.addEventListener('click', function() {
        const newContent = editContent.value;
        const formData = new FormData();
        formData.append('text', newContent);
        formData.append('attachments', JSON.stringify(currentAttachments));
    
        for (let file of editFiles.files) {
            formData.append('new_files', file);
        }
    
        fetch(`/edit_post/${currentPostId}`, {
            method: 'POST',
            body: formData
        })
        editForm.style.display = 'none';
        overlay.style.display = 'none';
        saveEdit.addEventListener('click', function() {
            const newContent = editContent.value;
            const formData = new FormData();
            formData.append('text', newContent);
            formData.append('attachments', JSON.stringify(currentAttachments));

            for (let file of editFiles.files) {
                formData.append('new_files', file);
            }

            fetch(`/edit_post/${currentPostId}`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === "OK") {
                    const postElement = document.querySelector(`.post[data-post-id="${currentPostId}"]`);
                    if (postElement) {
                        const contentElement = postElement.querySelector('.post-content');
                        if (contentElement) {
                            contentElement.textContent = newContent;
                        }

                        const attachmentsContainer = postElement.querySelector('.attachments');
                        if (attachmentsContainer) {
                            attachmentsContainer.innerHTML = '';
                            data.attachments.forEach(attachment => {
                                let attachmentElement;
                                if (attachment.file_type.startsWith('image/')) {
                                    attachmentElement = document.createElement('img');
                                    attachmentElement.src = `/static/uploads/${attachment.file_name}`;
                                    attachmentElement.alt = attachment.file_name;
                                } else if (attachment.file_type.startsWith('video/')) {
                                    attachmentElement = document.createElement('video');
                                    attachmentElement.controls = true;
                                    const source = document.createElement('source');
                                    source.src = `/static/uploads/${attachment.file_name}`;
                                    source.type = attachment.file_type;
                                    attachmentElement.appendChild(source);
                                } else if (attachment.file_type.startsWith('audio/')) {
                                    attachmentElement = document.createElement('audio');
                                    attachmentElement.controls = true;
                                    const source = document.createElement('source');
                                    source.src = `/static/uploads/${attachment.file_name}`;
                                    source.type = attachment.file_type;
                                    attachmentElement.appendChild(source);
                                } else {
                                    attachmentElement = document.createElement('a');
                                    attachmentElement.href = `/download_file/${attachment.file_name}`;
                                    attachmentElement.textContent = attachment.file_name;
                                    attachmentElement.download = '';
                                }
                                attachmentElement.dataset.id = attachment.id;
                                attachmentsContainer.appendChild(attachmentElement);
                            });
                        }
                    } else {
                        console.error(`Nie znaleziono posta o id: ${currentPostId}`);
                    }

                    editForm.style.display = 'none';
                    overlay.style.display = 'none';
                    alert(data.message);
                } else {
                    alert(`Błąd: ${data.message}`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert(`Wystąpił błąd podczas edycji posta: ${error.message}`);
            });
        });
            console.error('Error:', error);
            alert(`Wystąpił błąd podczas edycji posta: ${error.message}`);
        });

    cancelEdit.addEventListener('click', function() {
        editForm.style.display = 'none';
        overlay.style.display = 'none';
    });

    editFiles.addEventListener('change', function(e) {
        for (let file of e.target.files) {
            const attachmentDiv = document.createElement('div');
            attachmentDiv.className = 'attachment-preview';
            attachmentDiv.style.width = '100px';
            attachmentDiv.style.height = '100px';
            attachmentDiv.style.backgroundColor = 'blue';
            attachmentDiv.style.position = 'relative';
            attachmentDiv.style.display = 'inline-block';
            attachmentDiv.style.margin = '5px';

            const removeButton = document.createElement('button');
            removeButton.textContent = 'x';
            removeButton.style.position = 'absolute';
            removeButton.style.top = '0';
            removeButton.style.right = '0';
            removeButton.addEventListener('click', () => {
                attachmentDiv.remove();
            });

            attachmentDiv.appendChild(removeButton);
            existingAttachments.appendChild(attachmentDiv);
        }
    });
});