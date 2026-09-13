(() => {
  const form =
    document.getElementById("chatForm") ||
    document.getElementById("loginChatForm");
  const input =
    document.getElementById("chatInput") ||
    document.getElementById("loginChatInput");
  const messages =
    document.getElementById("chatMessages") ||
    document.getElementById("loginChatMessages");
  const panel =
    document.getElementById("chatbotPanel") ||
    document.getElementById("loginChatbot");
  const toggle = document.getElementById("chatbotToggle");
  const close = document.getElementById("chatbotClose");
  if (!form || !input || !messages) return;

  const history = [];
  const appendMessage = (text, type) => {
    const message = document.createElement("div");
    message.className = `message ${type}`;
    message.textContent = text;
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
    return message;
  };

  if (toggle && panel) {
    toggle.addEventListener("click", () => {
      panel.hidden = !panel.hidden;
      if (!panel.hidden) input.focus();
    });
  }

  if (close && panel) {
    close.addEventListener("click", () => {
      panel.hidden = true;
    });
  }

  document.querySelectorAll(".chat-suggestions button").forEach((button) => {
    button.addEventListener("click", () => {
      input.value = button.textContent;
      form.requestSubmit();
    });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    appendMessage(text, "user");
    input.value = "";
    input.disabled = true;
    const pending = appendMessage("Thinking...", "bot");
    const context = JSON.parse(
      localStorage.getItem("lioraCalculation") || "{}",
    );

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          history,
          context: {
            city: context.city || "",
            daily_kwh: String(context.daily || ""),
            system_kw: String(context.system || ""),
          },
        }),
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.detail || "The assistant is unavailable.");
      pending.textContent = data.answer;
      history.push(
        { role: "user", content: text },
        { role: "assistant", content: data.answer },
      );
      if (history.length > 20) history.splice(0, history.length - 20);
    } catch (error) {
      pending.textContent = error.message;
    } finally {
      input.disabled = false;
      input.focus();
    }
  });
})();
