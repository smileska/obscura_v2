function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
    const darkModeToggle = document.getElementById('darkModeToggle');

    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            const csrftoken = getCookie('csrftoken');

            fetch('/accounts/toggle-dark-mode/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({}),
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                if (data.dark_mode) {
                    document.body.classList.add('dark-mode');
                    darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
                } else {
                    document.body.classList.remove('dark-mode');
                    darkModeToggle.innerHTML = '<i class="fas fa-moon"></i>';
                }
            })
            .catch(error => {
                console.error('Error toggling dark mode:', error);
            });
        });
    }

    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});

function formatDateTime(dateString) {
    const date = new Date(dateString);
    const today = new Date();

    if (date.toDateString() === today.toDateString()) {
        return `Today at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }

    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    if (date.toDateString() === yesterday.toDateString()) {
        return `Yesterday at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }

    return date.toLocaleString([], {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function previewImage(input, previewElement) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function(e) {
            previewElement.src = e.target.result;
            previewElement.parentElement.classList.remove('hidden');
        };

        reader.readAsDataURL(input.files[0]);
    }
}

function scrollToBottom(element) {
    element.scrollTop = element.scrollHeight;
}

document.addEventListener('click', function(event) {
    if (event.target.closest('.reaction-button')) {
        event.preventDefault();
        event.stopPropagation();

        const button = event.target.closest('.reaction-button');
        const popup = button.nextElementSibling;

        document.querySelectorAll('.reaction-popup').forEach(p => {
            if (p !== popup) {
                p.classList.add('hidden');
            }
        });

        if (popup && popup.classList.contains('reaction-popup')) {
            popup.classList.toggle('hidden');
        }

        return;
    }

    if (event.target.closest('.reaction-popup button')) {
        event.preventDefault();
        event.stopPropagation();

        const emojiButton = event.target.closest('button');
        const message = emojiButton.closest('.message');

        if (message && emojiButton.dataset.reaction) {
            const messageId = message.dataset.messageId;
            const reactionType = emojiButton.dataset.reaction;

            if (typeof window.sendReaction === 'function') {
                window.sendReaction(messageId, reactionType);
            }

            emojiButton.closest('.reaction-popup').classList.add('hidden');
        }

        return;
    }

    if (!event.target.closest('.reaction-button') && !event.target.closest('.reaction-popup')) {
        document.querySelectorAll('.reaction-popup').forEach(popup => {
            popup.classList.add('hidden');
        });
    }
});

function getReactionEmoji(reactionType) {
    const reactions = {
        1: '👍',
        2: '❤️',
        3: '😂',
        4: '😮',
        5: '😢',
        6: '🐴',
        7: '🍮',
        8: '🌹'
    };
    return reactions[reactionType] || '<i class="far fa-smile"></i>';
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

window.updateMessageReaction = function(messageId, reactionType) {
    const message = document.querySelector(`.message[data-message-id="${messageId}"]`);
    if (!message) {
        return;
    }

    const reactionButton = message.querySelector('.reaction-button');
    if (reactionButton) {
        reactionButton.innerHTML = getReactionEmoji(reactionType);
    }
};

window.setupReactionButtons = function() {
    console.log('Using event delegation for reactions');
};