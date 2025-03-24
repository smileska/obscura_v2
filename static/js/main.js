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
    // Dark mode toggle functionality
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

    // Initialize Bootstrap tooltips
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // User search functionality
    const userSearchInput = document.getElementById('user-search');
    const searchBtn = document.getElementById('search-btn');
    const searchResults = document.getElementById('search-results');

    function performSearch() {
        const query = userSearchInput.value.trim();
        if (query.length < 2) {
            searchResults.innerHTML = '<div class="alert alert-info">Please enter at least 2 characters</div>';
            return;
        }

        // Show loading indicator
        searchResults.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Searching...</div>';

        fetch(`/chat/search-users/?q=${encodeURIComponent(query)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                searchResults.innerHTML = '';

                if (!data.users || data.users.length === 0) {
                    searchResults.innerHTML = '<div class="alert alert-info">No users found</div>';
                    return;
                }

                const resultsList = document.createElement('div');
                resultsList.className = 'list-group';

                data.users.forEach(user => {
                    const userItem = document.createElement('div');
                    userItem.className = 'list-group-item d-flex justify-content-between align-items-center';

                    const defaultImagePath = '/media/profile_pics/default.png';
                    const imageUrl = user.image || defaultImagePath;

                    userItem.innerHTML = `
                        <div>
                            <img src="${imageUrl}" class="rounded-circle me-2" width="30" height="30" onerror="this.src='${defaultImagePath}'">
                            <span>${user.username}</span>
                        </div>
                        <a href="/chat/${user.username}/" class="btn btn-sm btn-primary">Message</a>
                    `;

                    resultsList.appendChild(userItem);
                });

                searchResults.appendChild(resultsList);
            })
            .catch(error => {
                console.error('Error searching users:', error);
                searchResults.innerHTML = '<div class="alert alert-danger">An error occurred while searching. Please try again later.</div>';
            });
    }

    if (searchBtn) {
        searchBtn.addEventListener('click', performSearch);
    }

    if (userSearchInput) {
        userSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }

    // Handle user search in chatrooms
    const chatroomUserSearch = document.getElementById('user-search');
    const addUserBtn = document.getElementById('add-user-btn');
    const chatroomSearchResults = document.getElementById('search-results');

    if (chatroomUserSearch && addUserBtn) {
        chatroomUserSearch.addEventListener('input', function() {
            const query = this.value.trim();
            if (query.length < 2) {
                chatroomSearchResults.innerHTML = '';
                return;
            }

            fetch(`/chat/search-users/?q=${encodeURIComponent(query)}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    chatroomSearchResults.innerHTML = '';

                    if (!data.users || data.users.length === 0) {
                        chatroomSearchResults.innerHTML = '<div class="alert alert-info">No users found</div>';
                        return;
                    }

                    const resultsList = document.createElement('div');
                    resultsList.className = 'list-group';

                    data.users.forEach(user => {
                        const userItem = document.createElement('button');
                        userItem.className = 'list-group-item list-group-item-action';
                        userItem.textContent = user.username;
                        userItem.addEventListener('click', function() {
                            chatroomUserSearch.value = user.username;
                            chatroomSearchResults.innerHTML = '';
                        });

                        resultsList.appendChild(userItem);
                    });

                    chatroomSearchResults.appendChild(resultsList);
                })
                .catch(error => {
                    console.error('Error searching users:', error);
                    chatroomSearchResults.innerHTML = '<div class="alert alert-danger">An error occurred while searching</div>';
                });
        });
    }

    // Handle user suggestion in chatrooms
    const suggestSearchInput = document.getElementById('suggest-search');
    const suggestUserBtn = document.getElementById('suggest-user-btn');
    const suggestResults = document.getElementById('suggest-results');

    if (suggestSearchInput && suggestUserBtn) {
        suggestSearchInput.addEventListener('input', function() {
            const query = this.value.trim();
            if (query.length < 2) {
                suggestResults.innerHTML = '';
                return;
            }

            fetch(`/chat/search-users/?q=${encodeURIComponent(query)}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    suggestResults.innerHTML = '';

                    if (!data.users || data.users.length === 0) {
                        suggestResults.innerHTML = '<div class="alert alert-info">No users found</div>';
                        return;
                    }

                    const resultsList = document.createElement('div');
                    resultsList.className = 'list-group';

                    data.users.forEach(user => {
                        const userItem = document.createElement('button');
                        userItem.className = 'list-group-item list-group-item-action';
                        userItem.textContent = user.username;
                        userItem.addEventListener('click', function() {
                            suggestSearchInput.value = user.username;
                            suggestResults.innerHTML = '';
                        });

                        resultsList.appendChild(userItem);
                    });

                    suggestResults.appendChild(resultsList);
                })
                .catch(error => {
                    console.error('Error searching users:', error);
                    suggestResults.innerHTML = '<div class="alert alert-danger">An error occurred while searching</div>';
                });
        });
    }
});

// Date and time formatting utilities
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

function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Image preview functionality
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

// UI helpers
function scrollToBottom(element) {
    element.scrollTop = element.scrollHeight;
}

// Reaction functionality
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

// Handle reaction clicks using event delegation
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