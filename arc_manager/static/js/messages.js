// Función para remover mensajes duplicados
function removeDuplicateMessages() {
    const messages = document.querySelectorAll('.alert');
    const seenMessages = new Set();
    messages.forEach(message => {
        const messageText = message.textContent.trim();
        const cleanText = messageText.replace('×', '').trim();
        if (seenMessages.has(cleanText)) {
            message.remove();
        } else {
            seenMessages.add(cleanText);
        }
    });
}

document.addEventListener('DOMContentLoaded', removeDuplicateMessages);

const observer = new MutationObserver(removeDuplicateMessages);
observer.observe(document.body, { childList: true, subtree: true });

