<!-- Chatbot Widget -->
<style>
#chatbotWidgetBtn {
    position: fixed;
    bottom: 30px;
    right: 30px;
    z-index: 9999;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    border: none;
    border-radius: 50%;
    width: 60px; height: 60px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.18);
    cursor: pointer;
    font-size: 2rem;
    display: flex; align-items: center; justify-content: center;
}
#chatbotWidgetContainer {
    display: none;
    position: fixed;
    bottom: 100px;
    right: 30px;
    z-index: 10000;
    width: 370px;
    max-width: 95vw;
    height: 520px;
    background: white;
    border-radius: 18px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.18);
    overflow: hidden;
    flex-direction: column;
}
@media (max-width: 500px) {
    #chatbotWidgetContainer { width: 98vw; right: 1vw; }
}
</style>
<button id="chatbotWidgetBtn" title="Chat with us">🤖</button>
<div id="chatbotWidgetContainer">
    <!-- ...existing code from inside .chat-container in chatbot.php... -->
    <div class="chat-header">
        <h1 style="font-size:1.2em;">🤖 TOMAS</h1>
        <button onclick="closeChatbotWidget()" style="position:absolute;top:10px;right:15px;background:none;border:none;font-size:1.2em;color:#fff;cursor:pointer;">&times;</button>
        <p style="font-size:0.85em;">Ask me anything about our school!</p>
    </div>
    <div class="chat-messages" id="chatMessages">
        <div class="welcome-message">
            <p>👋 Hello! I'm Tomas. I'm here to help you with your questions. Feel free to ask me anything!</p>
        </div>
    </div>
<div class="chat-input-container">
    <div class="status-indicator" id="statusIndicator"></div>
    <div class="chat-input">
        <input type="text" id="messageInput" placeholder="Type your message here..." onkeypress="handleKeyPress(event)">
        <button class="send-btn" onclick="sendMessage()">
            <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                <path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/>
            </svg>
        </button>
    </div>
</div>
    <div class="powered-by" style="font-size:0.8em;">Powered by AI • Connected to live support</div>
</div>
<script>
let isWaitingForResponse = false;




document.getElementById('chatbotWidgetBtn').onclick = function () {
    document.getElementById('chatbotWidgetContainer').style.display = 'flex';
    setTimeout(() => document.getElementById('messageInput').focus(), 300);
};

function closeChatbotWidget() {
    document.getElementById('chatbotWidgetContainer').style.display = 'none';
}

function getCurrentTime() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function showStatus(message, type = 'success') {
    const indicator = document.getElementById('statusIndicator');
    indicator.textContent = message;
    indicator.className = `status-indicator ${type}`;
    setTimeout(() => { indicator.className = 'status-indicator'; }, 3000);
}

function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator active';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `<div class="typing-dots">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    </div>`;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) typingIndicator.remove();
}

function addMessage(sender, text, showTime = true) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    const time = showTime ? `<div class="message-time">${getCurrentTime()}</div>` : '';
    messageDiv.innerHTML = `<div class="message-content">${text}${time}</div>`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
    if (isWaitingForResponse) return;
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message) return;

    addMessage('user', message);
    input.value = '';
    showTypingIndicator();
    isWaitingForResponse = true;

    try {
        const response = await fetch('https://tomaschatbot.onrender.com/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: message })
        });
        const data = await response.json();
        hideTypingIndicator();
        addMessage('bot', data.response);
    } catch (error) {
        hideTypingIndicator();
        addMessage('bot', 'Sorry, I encountered an error. Please try again later.');
        showStatus('Connection error. Please try again.', 'error');
    }

    isWaitingForResponse = false;
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}
</script>

<!-- Chatbot widget styles (reuse from chatbot.php) -->
<style>
/* ...copy the relevant CSS from chatbot.php for .chat-header, .chat-messages, .message, etc... */
.chat-header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 16px 20px 12px 20px; text-align: center; position:relative; }
.chat-header h1 { font-size: 1.2em; margin-bottom: 2px; }
.chat-header p { opacity: 0.9; font-size: 0.85em; }
.chat-messages { flex: 1; padding: 16px; overflow-y: auto; background: #f8f9fa; scroll-behavior: smooth; height: 260px; }
.message { margin-bottom: 12px; display: flex; align-items: flex-start; animation: slideIn 0.3s ease; }
.message.user { justify-content: flex-end; }
.message.bot { justify-content: flex-start; }
.message-content { max-width: 70%; padding: 10px 15px; border-radius: 18px; word-wrap: break-word; position: relative; }
.message.user .message-content { background: #667eea; color: white; border-bottom-right-radius: 4px; }
.message.bot .message-content { background: white; color: #333; border: 1px solid #e0e0e0; border-bottom-left-radius: 4px; }
.message-time { font-size: 0.7em; opacity: 0.7; margin-top: 5px; }
.typing-indicator { display: none; align-items: center; padding: 10px 18px; background: white; border-radius: 18px; border: 1px solid #e0e0e0; max-width: 70px; margin-bottom: 15px; }
.typing-indicator.active { display: flex; }
.typing-dots { display: flex; gap: 3px; }
.typing-dot { width: 6px; height: 6px; border-radius: 50%; background: #667eea; animation: typing 1.4s infinite; }
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
.chat-input-container { background: white; padding: 12px 16px; border-top: 1px solid #e0e0e0; }
.form-row input:focus { border-color: #667eea; }
.chat-input { display: flex; align-items: center; gap: 8px; }
.chat-input input { flex: 1; padding: 10px 15px; border: 1px solid #e0e0e0; border-radius: 25px; font-size: 1em; outline: none; transition: border-color 0.3s; }
.chat-input input:focus { border-color: #667eea; }
.send-btn { background: #667eea; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.3s, transform 0.2s; }
.send-btn:hover { background: #5a6fd8; transform: scale(1.05); }
.send-btn:active { transform: scale(0.95); }
.status-indicator { display: none; padding: 8px 12px; border-radius: 10px; margin-bottom: 8px; font-size: 0.9em; text-align: center; }
.status-indicator.success { display: block; background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.status-indicator.error { display: block; background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
@keyframes slideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes typing { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-10px); } }
.welcome-message { text-align: center; padding: 10px; color: #666; font-style: italic; }
.powered-by { text-align: center; padding: 6px; font-size: 0.8em; color: #999; background: #f8f9fa; border-top: 1px solid #e0e0e0; }
</style>
