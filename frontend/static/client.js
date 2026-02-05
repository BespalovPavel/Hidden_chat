const appData = document.getElementById("app-data");
const roomId = appData.dataset.roomId;
const username = appData.dataset.username;
const userId = appData.dataset.userId;

const messagesContainer = document.getElementById("messages");
const messageInput = document.getElementById("messageInput");
const statusDiv = document.getElementById("status");

const protocol = window.location.protocol === "https:" ? "wss" : "ws"

const ws = new WebSocket(`${protocol}://${window.location.host}/ws/${roomId}/${userId}?username=${username}`);


ws.onopen = () => {
    console.log("WebSocket connected")
    statusDiv.innerHTML = `
        <div class="flex items-center gap-2">
            <span class="w-2 h-2 bg-green-500 rounded-full shadow-sm shadow-green-300"></span>
            <span class="text-green-600 font-medium text-sm">Онлайн</span>
        </div>
    `;
};

ws.onclose = () => {
    console.log("WebSocket disconnected")
    statusDiv.innerHTML = `
        <div class="flex items-center gap-2">
            <span class="w-2 h-2 bg-red-500 rounded-full shadow-sm shadow-red-300"></span>
            <span class="text-red-600 font-medium text-sm">Отключено</span>
        </div>
    `;

    renderSystemMessage("Соединение с сервером потеряно");
}

ws.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data);
        
        if (data.type === "system") {
            renderSystemMessage(data.text);
        } else {
            const isSelf = String(data.user_id) === String(userId);
            renderMessage(data, isSelf);
        }
        
        scrollToBottom();
    } catch (e) {
        console.error("Ошибка парсинга JSON:", e);
    }
};

function renderMessage(data, isSelf) {
    const wrapper = document.createElement("div");
    wrapper.className = `flex w-full ${isSelf ? 'justify-end' : 'justify-start'}`;

    const bubble = document.createElement("div");
    bubble.className = `max-w-[75%] px-4 py-2 rounded-2xl shadow-sm break-words ${
        isSelf 
        ? 'bg-blue-600 text-white rounded-br-none' 
        : 'bg-white text-slate-800 border border-slate-100 rounded-bl-none'
    }`;

    if (!isSelf) {
        const author = document.createElement("div");
        author.className = "text-xs text-slate-400 mb-1 ml-1";
        author.textContent = data.username; 
        bubble.appendChild(author);
    }

    const textNode = document.createElement("div");
    textNode.textContent = data.text; 
    bubble.appendChild(textNode);

    const time = document.createElement("div");
    const date = new Date(data.timestamp);

    time.className = `text-[10px] mt-1 text-right ${isSelf ? 'text-blue-200' : 'text-slate-400'}`;
    time.textContent = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    bubble.appendChild(time)

    wrapper.appendChild(bubble);
    messagesContainer.appendChild(wrapper);
}

function renderSystemMessage(text) {
    const wrapper = document.createElement("div");
    wrapper.className = "flex justify-center my-4";
    
    const badge = document.createElement("span");
    badge.className = "bg-slate-200 text-slate-500 text-xs px-3 py-1 rounded-full";
    badge.textContent = text;
    
    wrapper.appendChild(badge);
    messagesContainer.appendChild(wrapper);
}


function sendMessage () {
    const text = messageInput.value.trim()

    if(text){
        ws.send(JSON.stringify({ message: text }));
        messageInput.value = "";
        messageInput.focus();
    }

}


function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});

