document.addEventListener('DOMContentLoaded', () => {
    // Check if we have chat history in session storage to restore state
    // For a simple prototype, we might skip full history restoration or implement later.
});

function toggleChat() {
    const widget = document.getElementById('chat-widget');
    const icon = document.getElementById('chat-toggle-icon');
    widget.classList.toggle('minimized');
    
    if (widget.classList.contains('minimized')) {
        icon.textContent = '▲';
    } else {
        icon.textContent = '▼';
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    // Add user message
    addMessageToChat(message, 'user');
    input.value = '';

    // Show loading...
    const loadingId = addMessageToChat('Thinking...', 'ai', true);

    try {
        const response = await fetch('/chat_generate_rule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: message })
        });

        const data = await response.json();
        
        // Remove loading
        removeMessage(loadingId);

        if (data.error) {
            addMessageToChat('Error: ' + data.error, 'ai');
        } else {
            // Display AI response text
            addMessageToChat(data.message, 'ai');
            
            // If a rule object was returned, show it with approve/reject buttons
            if (data.rule_obj) {
                addRuleApprovalCard(data.rule_obj);
            }
        }
    } catch (e) {
        removeMessage(loadingId);
        addMessageToChat('Network Error: ' + e.message, 'ai');
    }
}

function addMessageToChat(text, sender, isLoading = false) {
    const chatBody = document.getElementById('chat-body');
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    div.textContent = text;
    
    if (isLoading) {
        div.id = 'loading-msg';
        div.style.fontStyle = 'italic';
        div.style.color = '#888';
    }
    
    chatBody.appendChild(div);
    chatBody.scrollTop = chatBody.scrollHeight;
    return div.id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function addRuleApprovalCard(ruleObj) {
    const chatBody = document.getElementById('chat-body');
    const div = document.createElement('div');
    div.className = 'message ai';
    div.style.display = 'flex';
    div.style.flexDirection = 'column';
    div.style.gap = '5px';
    div.style.border = '1px solid #4a90e2';
    div.style.backgroundColor = '#eef6ff';

    const title = document.createElement('strong');
    title.textContent = "Generated Rule:";
    div.appendChild(title);

    const desc = document.createElement('div');
    desc.style.fontSize = '12px';
    desc.innerHTML = `<b>ID:</b> ${ruleObj.rule_id}<br><b>Desc:</b> ${ruleObj.rule_description}`;
    div.appendChild(desc);
    
    // Display SQL Query
    const sqlContainer = document.createElement('div');
    sqlContainer.style.fontSize = '11px';
    sqlContainer.style.fontFamily = 'monospace';
    sqlContainer.style.backgroundColor = '#f0f0f0';
    sqlContainer.style.padding = '8px';
    sqlContainer.style.borderRadius = '4px';
    sqlContainer.style.whiteSpace = 'pre-wrap';
    sqlContainer.style.maxHeight = '150px';
    sqlContainer.style.overflowY = 'auto';
    sqlContainer.style.border = '1px solid #ddd';
    sqlContainer.style.marginTop = '5px';
    sqlContainer.textContent = ruleObj.sql;
    div.appendChild(sqlContainer);
    
    const controls = document.createElement('div');
    controls.className = 'chat-controls';
    
    const approveBtn = document.createElement('button');
    approveBtn.textContent = '✅ Approve & Add to Session';
    approveBtn.style.backgroundColor = '#28a745';
    approveBtn.style.color = 'white';
    approveBtn.style.border = 'none';
    approveBtn.style.cursor = 'pointer';
    
    approveBtn.onclick = function() {
        approveRule(ruleObj, div);
    };

    controls.appendChild(approveBtn);
    div.appendChild(controls);

    chatBody.appendChild(div);
    chatBody.scrollTop = chatBody.scrollHeight;
}

async function approveRule(ruleObj, cardElement) {
    try {
        const response = await fetch('/chat_approve_rule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rule: ruleObj })
        });
        
        const data = await response.json();
        
        if (data.success) {
            cardElement.innerHTML = `✅ <b>Rule Approved!</b><br>ID: ${ruleObj.rule_id}<br>It will be included in the next run.`;
            cardElement.style.borderColor = '#28a745';
            cardElement.style.backgroundColor = '#d4edda';
        } else {
            alert('Error saving rule: ' + data.error);
        }
    } catch (e) {
        alert('Network error approving rule');
    }
}
