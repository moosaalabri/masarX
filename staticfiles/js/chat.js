document.addEventListener('DOMContentLoaded', function() {
    const chatWidget = document.getElementById('masar-chat-widget');
    const chatToggle = document.getElementById('masar-chat-toggle');
    const chatClose = document.getElementById('masar-chat-close');
    const chatForm = document.getElementById('masar-chat-form');
    const chatInput = document.getElementById('masar-chat-input');
    const chatMessages = document.getElementById('masar-chat-messages');

    if (!chatWidget) return;

    // Toggle Chat
    function toggleChat() {
        if (chatWidget.classList.contains('d-none')) {
            chatWidget.classList.remove('d-none');
            setTimeout(() => chatInput.focus(), 100);
        } else {
            chatWidget.classList.add('d-none');
        }
    }

    chatToggle.addEventListener('click', toggleChat);
    chatClose.addEventListener('click', toggleChat);

    // Send Message
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!message) return;

        // Add User Message
        addMessage(message, 'user');
        chatInput.value = '';

        // Show Typing Indicator
        const typingId = addTypingIndicator();

        // Send to Backend
        fetch('/ajax/chatbot/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                message: message,
                language: document.documentElement.lang || 'en'
            })
        })
        .then(response => response.json())
        .then(data => {
            removeMessage(typingId);
            if (data.success) {
                addMessage(data.response, 'bot');
            } else {
                addMessage('Sorry, I encountered an error.', 'bot');
            }
        })
        .catch(error => {
            removeMessage(typingId);
            addMessage('Sorry, connection error.', 'bot');
            console.error('Error:', error);
        });
    });

    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.className = `d-flex mb-3 ${sender === 'user' ? 'justify-content-end' : 'justify-content-start'}`;
        
        const bubble = document.createElement('div');
        bubble.className = `p-3 rounded-3 shadow-sm ${sender === 'user' ? 'bg-primary text-white' : 'bg-light text-dark'}`;
        bubble.style.maxWidth = '80%';
        bubble.style.wordWrap = 'break-word';
        // Convert newlines to <br> for basic formatting
        bubble.innerHTML = text.replace(/\n/g, '<br>');

        div.appendChild(bubble);
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return div.id;
    }

    function addTypingIndicator() {
        const id = 'typing-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'd-flex mb-3 justify-content-start';
        div.innerHTML = ""
            + "<div class=\"bg-light p-3 rounded-3 shadow-sm\">"
            + "    <div class=\"typing-dots\">"
            + "        <span></span><span></span><span></span>"
            + "    </div>"
            + "</div>"
        ;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }

    function removeMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

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
});
