    <!-- Chat Widget -->
    <button id="masar-chat-toggle" class="d-flex align-items-center justify-content-center">
        <i class="bi bi-chat-dots-fill fs-4"></i>
    </button>

    <div id="masar-chat-widget" class="d-none bg-white rounded-4 shadow overflow-hidden">
        <div class="bg-dark text-white p-3 d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center">
                <i class="bi bi-robot me-2 fs-5"></i>
                <h6 class="mb-0 fw-bold">MasarX AI</h6>
            </div>
            <button id="masar-chat-close" class="btn btn-sm btn-link text-white p-0">
                <i class="bi bi-x-lg"></i>
            </button>
        </div>
        
        <div id="masar-chat-messages" class="flex-grow-1 p-3 bg-light overflow-auto">
            <div class="d-flex mb-3 justify-content-start">
                <div class="p-3 rounded-3 shadow-sm bg-light text-dark" style="max-width: 80%;">
                    {% trans "Hello! How can I help you with your shipments today?" %}
                </div>
            </div>
        </div>
        
        <div class="p-3 border-top bg-white">
            <form id="masar-chat-form" class="d-flex">
                <input type="text" id="masar-chat-input" class="form-control me-2" placeholder="{% trans 'Type a message...' %}" autocomplete="off">
                <button type="submit" class="btn btn-masarx-primary px-3">
                    <i class="bi bi-send-fill"></i>
                </button>
            </form>
        </div>
    </div>
    
    <script src="{% static 'js/chat.js' %}?v={{ deployment_timestamp }}"></script>
</body>