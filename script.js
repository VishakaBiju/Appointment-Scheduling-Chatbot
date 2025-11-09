const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

const API_URL = "http://127.0.0.1:8000/message";
const USER_ID = "user123"; // can make dynamic later

//  Function to get current time in hh:mm AM/PM format
function getCurrentTime() {
  const now = new Date();
  return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

//  Add message to chat
function addMessage(text, sender = "bot", buttons = []) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add(sender === "bot" ? "bot-message" : "user-message");

  //  Format line breaks
  messageDiv.innerHTML = text.replace(/\n/g, "<br>");

  //  Add timestamp
  const timeSpan = document.createElement("div");
  timeSpan.classList.add("timestamp");
  timeSpan.textContent = getCurrentTime();

  // Append both
  messageDiv.appendChild(timeSpan);
  chatBox.appendChild(messageDiv);

  // Add buttons if provided
  if (buttons.length > 0) {
    const btnContainer = document.createElement("div");
    btnContainer.classList.add("button-container");

    buttons.forEach((btnText) => {
      const btn = document.createElement("button");
      btn.textContent = btnText;
      btn.onclick = () => sendMessage(btnText);
      btnContainer.appendChild(btn);
    });

    chatBox.appendChild(btnContainer);
  }

  chatBox.scrollTop = chatBox.scrollHeight;
  saveChatHistory();

}

//  Typing indicator
function showTyping() {
  const typingDiv = document.createElement("div");
  typingDiv.classList.add("bot-message", "typing");
  typingDiv.innerHTML = "💬 Bot is typing...";
  chatBox.appendChild(typingDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
  return typingDiv;
}

//  Send message to backend
async function sendMessage(message) {
  if (!message.trim()) return;

  addMessage(message, "user");
  userInput.value = "";

  // show typing indicator
  const typingDiv = showTyping();

  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: USER_ID, text: message }),
  });

  const data = await response.json();

  // remove typing indicator
  typingDiv.remove();

  addMessage(data.reply, "bot", data.buttons || []);
}

// auto-load welcome message on startup
loadChatHistory();
window.onload = async () => {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: USER_ID, text: "start" }),
  });
  const data = await response.json();
  addMessage(data.reply, "bot", data.buttons || []);
};

// Send message on click or Enter
sendBtn.onclick = () => sendMessage(userInput.value);
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage(userInput.value);
});
 // save and load chat hostory  
function saveChatHistory() {
  const messages = chatBox.innerHTML;
  localStorage.setItem("chatHistory", messages);
}

function loadChatHistory() {
  const saved = localStorage.getItem("chatHistory");
  if (saved) chatBox.innerHTML = saved;
}
