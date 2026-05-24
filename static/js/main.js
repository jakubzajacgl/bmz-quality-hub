document.addEventListener("DOMContentLoaded", () => {
    // Logika chmurki chatbota
    const chatbotContainer = document.getElementById("chatbot-container");
    const chatbotBubble = document.getElementById("chatbot-bubble");
    const chatClose = document.getElementById("chat-close");

    // Otwieranie
    chatbotBubble.addEventListener("click", () => {
        chatbotContainer.classList.add("open");
    });

    // Zamykanie
    chatClose.addEventListener("click", () => {
        chatbotContainer.classList.remove("open");
    });

    // Logika wiadomości
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("chat-send");
    const chatMessages = document.getElementById("chat-messages");

    function addMessage(text, sender) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `msg ${sender}-msg`;
        msgDiv.textContent = text;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        addMessage(text, "user");
        chatInput.value = "";

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();

            setTimeout(() => {
                addMessage(data.response, "bot");

                if (data.target) {
                    const targetCard = document.getElementById(`card-${data.target}`);
                    if (targetCard) {
                        targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        targetCard.classList.add('highlight-card');
                        setTimeout(() => {
                            targetCard.classList.remove('highlight-card');
                        }, 2500);
                    }
                }
            }, 600);

        } catch (error) {
            addMessage("Błąd połączenia z serwerem.", "bot");
        }
    }

    sendBtn.addEventListener("click", sendMessage);
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });
});