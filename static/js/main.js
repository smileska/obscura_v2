// Utility functions
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

// Get reaction emoji based on type
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

// Image preview functionality
function handleImageUpload(input, previewElement, previewContainer) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function(e) {
            previewElement.src = e.target.result;
            previewContainer.classList.remove('d-none');

            // Limit preview image size
            previewElement.style.maxWidth = '180px';
            previewElement.style.maxHeight = '180px';
        };

        reader.readAsDataURL(input.files[0]);
    }
}

// UI helpers
function scrollToBottom(element) {
    element.scrollTop = element.scrollHeight;
}

// Update message reaction in UI
window.updateMessageReaction = function(messageId, reactionType) {
    const message = document.querySelector(`.message[data-message-id="${messageId}"]`);
    if (!message) {
        return;
    }

    const reactionButton = message.querySelector('.reaction-button');
    if (reactionButton) {
        reactionButton.innerHTML = getReactionEmoji(reactionType);

        // Close any open reaction popups
        const popup = message.querySelector('.reaction-popup');
        if (popup) {
            popup.classList.add('hidden');
        }
    }
};

// Force full viewport height and fix layout issues
function forceFullViewport() {
    // Get viewport dimensions
    const viewportHeight = window.innerHeight;

    // Set body and html to full height
    document.documentElement.style.height = '100%';
    document.body.style.height = '100%';
    document.body.style.overflow = 'hidden';

    // Get main container
    const container = document.querySelector('.container-fluid') || document.querySelector('.container');
    if (container) {
        // Account for navbar
        const navbar = document.querySelector('.navbar');
        const navbarHeight = navbar ? navbar.offsetHeight : 60;

        // Set container height
        container.style.height = `calc(100vh - ${navbarHeight + 20}px)`;
        container.style.display = 'flex';
        container.style.flexDirection = 'column';

        // Set row to flex
        const row = container.querySelector('.row');
        if (row) {
            row.style.flex = '1';
            row.style.display = 'flex';

            // Set column to flex
            const col = row.querySelector('.col-md-8') || row.querySelector('.col-md-9');
            if (col) {
                col.style.flex = '1';
                col.style.display = 'flex';
                col.style.flexDirection = 'column';

                // Set card to flex
                const card = col.querySelector('.card');
                if (card) {
                    card.style.flex = '1';
                    card.style.display = 'flex';
                    card.style.flexDirection = 'column';
                    card.style.marginBottom = '0';

                    // Get card header and calculate its height
                    const cardHeader = card.querySelector('.card-header');
                    const headerHeight = cardHeader ? cardHeader.offsetHeight : 0;

                    // Get form and calculate its height
                    const messageForm = card.querySelector('#message-form');
                    const formHeight = messageForm ? messageForm.offsetHeight : 0;

                    // Set card body to flex
                    const cardBody = card.querySelector('.card-body');
                    if (cardBody) {
                        cardBody.style.flex = '1';
                        cardBody.style.display = 'flex';
                        cardBody.style.flexDirection = 'column';
                        cardBody.style.overflow = 'hidden';

                        // Calculate chat box height
                        const cardBodyPadding = 32; // top and bottom padding
                        const chatBoxMargin = 16;   // bottom margin
                        const availableHeight = viewportHeight - navbarHeight - headerHeight - formHeight - cardBodyPadding - chatBoxMargin;

                        // Find chat box and set its height
                        const chatBox = cardBody.querySelector('.chat-box');
                        if (chatBox) {
                            chatBox.style.flex = '1';
                            chatBox.style.minHeight = '0'; // Important for flexbox
                            chatBox.style.height = 'auto';
                            chatBox.style.maxHeight = 'none';

                            // Force scroll to bottom
                            setTimeout(function() {
                                chatBox.scrollTop = chatBox.scrollHeight;
                            }, 100);
                        }
                    }
                }
            }
        }
    }
}

// Apply specific styling to message components
function applyStylesToMessages() {
    // Style sent messages
    document.querySelectorAll('.message-sent').forEach(message => {
        // Make container transparent
        message.style.backgroundColor = 'transparent';

        // Style bubble
        const bubble = message.querySelector('.message-bubble');
        if (bubble) {
            bubble.style.backgroundColor = '#7e3ff2';
            bubble.style.color = 'white';
            bubble.style.alignSelf = 'flex-end';
            bubble.style.marginLeft = 'auto';
            bubble.style.borderBottomRightRadius = '4px';
        }

        // Style reaction container
        const reactionContainer = message.querySelector('.reaction-container');
        if (reactionContainer) {
            reactionContainer.style.display = 'flex';
            reactionContainer.style.justifyContent = 'flex-end';
            reactionContainer.style.position = 'relative';
            reactionContainer.style.zIndex = '100';
        }

        // Style reaction button
        const reactionButton = message.querySelector('.reaction-button');
        if (reactionButton) {
            reactionButton.style.visibility = 'visible';
            reactionButton.style.opacity = '1';
            reactionButton.style.marginRight = '8px';
        }
    });

    // Style received messages
    document.querySelectorAll('.message-received').forEach(message => {
        // Make container transparent
        message.style.backgroundColor = 'transparent';

        // Style bubble
        const bubble = message.querySelector('.message-bubble');
        if (bubble) {
            // Make bubble darker
            bubble.style.backgroundColor = '#d0d0d0';
            bubble.style.color = '#000000';
            bubble.style.alignSelf = 'flex-start';
            bubble.style.marginRight = 'auto';
            bubble.style.borderBottomLeftRadius = '4px';
            // Ensure minimum width
            bubble.style.minWidth = '120px';
            bubble.style.display = 'inline-block';

            // Adjust for dark mode if needed
            if (document.body.classList.contains('dark-mode')) {
                bubble.style.backgroundColor = '#444444';
                bubble.style.color = '#ffffff';
            }
        }

        // Style reaction container - align to left
        const reactionContainer = message.querySelector('.reaction-container');
        if (reactionContainer) {
            reactionContainer.style.display = 'flex';
            reactionContainer.style.justifyContent = 'flex-start';
            reactionContainer.style.position = 'relative';
            reactionContainer.style.zIndex = '100';
            reactionContainer.style.marginTop = '2px';
            reactionContainer.style.width = '100%';
            reactionContainer.style.minHeight = '30px';
        }

        // Style reaction button - position on left
        const reactionButton = message.querySelector('.reaction-button');
        if (reactionButton) {
            reactionButton.style.visibility = 'visible';
            reactionButton.style.opacity = '1';
            reactionButton.style.marginLeft = '8px';
            reactionButton.style.marginRight = '0';
            reactionButton.style.zIndex = '101';
            reactionButton.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
            reactionButton.style.border = '1px solid rgba(0, 0, 0, 0.1)';
            reactionButton.style.borderRadius = '50%';
            reactionButton.style.width = '28px';
            reactionButton.style.height = '28px';
            reactionButton.style.display = 'flex';
            reactionButton.style.alignItems = 'center';
            reactionButton.style.justifyContent = 'center';
            reactionButton.style.fontSize = '14px';
            reactionButton.style.cursor = 'pointer';
            reactionButton.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.2)';
        }

        // Style reaction popup - position on left
        const reactionPopup = message.querySelector('.reaction-popup');
        if (reactionPopup) {
            reactionPopup.style.position = 'absolute';
            reactionPopup.style.bottom = '30px';
            reactionPopup.style.left = '0';
            reactionPopup.style.right = 'auto';
            reactionPopup.style.minWidth = '250px';
            reactionPopup.style.padding = '8px 12px';
            reactionPopup.style.backgroundColor = document.body.classList.contains('dark-mode') ? '#333' : 'white';
            reactionPopup.style.borderRadius = '20px';
            reactionPopup.style.zIndex = '999';
            reactionPopup.style.display = 'flex';
            reactionPopup.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.15)';
            reactionPopup.style.border = '1px solid rgba(0, 0, 0, 0.1)';

            // Ensure emoji buttons have proper size
            const buttons = reactionPopup.querySelectorAll('button');
            buttons.forEach(button => {
                button.style.width = '36px';
                button.style.height = '36px';
                button.style.fontSize = '18px';
                button.style.margin = '0 4px';
                button.style.background = 'transparent';
                button.style.border = 'none';
                button.style.display = 'flex';
                button.style.alignItems = 'center';
                button.style.justifyContent = 'center';
                button.style.cursor = 'pointer';
                button.style.borderRadius = '50%';
            });
        }
    });
}

// Fix image sizes
function setupImageSizes() {
    document.querySelectorAll('.message-image').forEach(img => {
        img.style.maxWidth = '250px';
        img.style.maxHeight = '180px';
        img.style.objectFit = 'contain';
        img.style.borderRadius = '8px';
        img.style.marginTop = '4px';

        img.addEventListener('load', function() {
            // Scroll chat to bottom after image loads
            const chatBox = this.closest('.chat-box');
            if (chatBox) {
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        });
    });
}

// Handle reaction button clicks
function setupReactionHandlers() {
    // Add click handler for reaction buttons
    document.querySelectorAll('.reaction-button').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const popup = this.nextElementSibling;

            // Close all other popups
            document.querySelectorAll('.reaction-popup').forEach(p => {
                if (p !== popup) {
                    p.classList.add('hidden');
                }
            });

            // Toggle this popup
            if (popup && popup.classList.contains('reaction-popup')) {
                popup.classList.toggle('hidden');

                // Force proper styling when visible
                if (!popup.classList.contains('hidden')) {
                    popup.style.display = 'flex';
                    popup.style.visibility = 'visible';
                    popup.style.opacity = '1';
                    popup.style.zIndex = '10001'; // Highest z-index
                }
            }
        });
    });

    // Add click handler for emoji buttons
    document.querySelectorAll('.reaction-popup button').forEach(emojiButton => {
        emojiButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const popup = this.closest('.reaction-popup');
            const message = this.closest('.message') ||
                           this.closest('.message-sent') ||
                           this.closest('.message-received');

            if (message && this.dataset.reaction) {
                const messageId = message.dataset.messageId;
                const reactionType = this.dataset.reaction;

                // Send reaction if function exists
                if (typeof window.sendReaction === 'function') {
                    window.sendReaction(messageId, reactionType);
                }

                // Hide popup
                popup.classList.add('hidden');
            }
        });
    });

    // Close popups when clicking elsewhere
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.reaction-popup') && !e.target.closest('.reaction-button')) {
            document.querySelectorAll('.reaction-popup').forEach(popup => {
                popup.classList.add('hidden');
            });
        }
    });
}

// Fix reaction panels specifically for received messages
function fixReceivedMessageReactions() {
    document.querySelectorAll('.message-received').forEach(message => {
        const reactionContainer = message.querySelector('.reaction-container');
        const reactionButton = message.querySelector('.reaction-button');
        const reactionPopup = message.querySelector('.reaction-popup');

        if (reactionContainer) {
            // Fix container
            reactionContainer.style.display = 'flex';
            reactionContainer.style.justifyContent = 'flex-start';
            reactionContainer.style.width = '100%';
            reactionContainer.style.position = 'relative';
            reactionContainer.style.zIndex = '100';
            reactionContainer.style.minHeight = '30px';
        }

        if (reactionButton) {
            // Fix button
            reactionButton.style.visibility = 'visible';
            reactionButton.style.opacity = '1';
            reactionButton.style.display = 'flex';
            reactionButton.style.marginLeft = '8px';
            reactionButton.style.marginRight = '0';
            reactionButton.style.zIndex = '101';
            reactionButton.style.backgroundColor = document.body.classList.contains('dark-mode') ?
                'rgba(70, 70, 70, 0.9)' : 'rgba(255, 255, 255, 0.9)';
        }

        if (reactionPopup) {
            // Fix popup
            reactionPopup.style.position = 'absolute';
            reactionPopup.style.bottom = '30px';
            reactionPopup.style.left = '0';
            reactionPopup.style.right = 'auto';
            reactionPopup.style.zIndex = '10001';

            // Force proper styling when visible
            if (!reactionPopup.classList.contains('hidden')) {
                reactionPopup.style.display = 'flex';
                reactionPopup.style.visibility = 'visible';
                reactionPopup.style.opacity = '1';
            }
        }
    });
}

// Master function to apply all fixes
function applyAllFixes() {
    forceFullViewport();
    applyStylesToMessages();
    setupImageSizes();
    setupReactionHandlers();
    fixReceivedMessageReactions();
}

// Dark mode toggle
function setupDarkModeToggle() {
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
                // Re-apply styles when toggling dark mode
                applyAllFixes();
            })
            .catch(error => {
                console.error('Error toggling dark mode:', error);
            });
        });
    }
}

// User search functionality
function setupUserSearch() {
    const userSearchInput = document.getElementById('user-search');
    const searchBtn = document.getElementById('search-btn');
    const searchResults = document.getElementById('search-results');

    if (userSearchInput && searchBtn && searchResults) {
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

        searchBtn.addEventListener('click', performSearch);

        userSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
}

// Setup chatroom user search and management
function setupChatroomFunctions() {
    // Chatroom user search
    const chatroomUserSearch = document.getElementById('user-search');
    const addUserBtn = document.getElementById('add-user-btn');
    const chatroomSearchResults = document.getElementById('search-results');

    if (chatroomUserSearch && addUserBtn && chatroomSearchResults) {
        chatroomUserSearch.addEventListener('input', function() {
            const query = this.value.trim();
            if (query.length < 2) {
                chatroomSearchResults.innerHTML = '';
                return;
            }

            fetch(`/chat/search-users/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
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

    // Chatroom user suggestion
    const suggestSearchInput = document.getElementById('suggest-search');
    const suggestUserBtn = document.getElementById('suggest-user-btn');
    const suggestResults = document.getElementById('suggest-results');

    if (suggestSearchInput && suggestUserBtn && suggestResults) {
        suggestSearchInput.addEventListener('input', function() {
            const query = this.value.trim();
            if (query.length < 2) {
                suggestResults.innerHTML = '';
                return;
            }

            fetch(`/chat/search-users/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
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

    // Leave chatroom button
    const leaveBtn = document.getElementById('leave-btn');
    if (leaveBtn) {
        leaveBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to leave this chatroom?')) {
                const chatroomId = new URLSearchParams(window.location.search).get('id') ||
                                 window.location.pathname.split('/').filter(Boolean).pop();
                const csrftoken = getCookie('csrftoken');

                fetch(`/chatrooms/${chatroomId}/leave/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.href = '/chatrooms/';
                    } else {
                        alert(data.error || 'An error occurred');
                    }
                })
                .catch(error => console.error('Error leaving chatroom:', error));
            }
        });
    }
}

// Main initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all functionality
    applyAllFixes();
    setupDarkModeToggle();
    setupUserSearch();
    setupChatroomFunctions();

    // Setup window resize event
    window.addEventListener('resize', applyAllFixes);

    // Create a mutation observer to detect DOM changes
    const observer = new MutationObserver(function(mutations) {
        let needsFixing = false;

        mutations.forEach(mutation => {
            // Check if we added new messages
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                for (let i = 0; i < mutation.addedNodes.length; i++) {
                    const node = mutation.addedNodes[i];
                    // Check if the added node is a message or contains messages
                    if (node.nodeType === 1 && ( // Element node
                        node.classList.contains('message-sent') ||
                        node.classList.contains('message-received') ||
                        node.querySelector('.message-sent') ||
                        node.querySelector('.message-received')
                    )) {
                        needsFixing = true;
                        break;
                    }
                }
            }

            // Check for class changes to reaction popups
            if (mutation.type === 'attributes' &&
                mutation.attributeName === 'class' &&
                mutation.target.classList.contains('reaction-popup')) {
                needsFixing = true;
            }
        });

        if (needsFixing) {
            // Only fix the reactions to avoid performance issues
            fixReceivedMessageReactions();
            setupReactionHandlers();
        }
    });

    // Start observing changes to the chat boxes
    const chatBoxes = document.querySelectorAll('.chat-box');
    chatBoxes.forEach(chatBox => {
        if (chatBox) {
            observer.observe(chatBox, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['class']
            });
        }
    });

    // Special handling for reaction button hover effects
    document.querySelectorAll('.reaction-button').forEach(button => {
        button.addEventListener('mouseover', function() {
            this.style.transform = 'scale(1.2)';
            this.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.3)';
        });

        button.addEventListener('mouseout', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
        });
    });

    // Special handling for emoji button hover effects
    document.querySelectorAll('.reaction-popup button').forEach(button => {
        button.addEventListener('mouseover', function() {
            this.style.transform = 'scale(1.2)';
            this.style.backgroundColor = 'rgba(0, 0, 0, 0.05)';
        });

        button.addEventListener('mouseout', function() {
            this.style.transform = '';
            this.style.backgroundColor = '';
        });
    });
});