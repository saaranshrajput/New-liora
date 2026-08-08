const signupForm = document.getElementById("signupForm");
const signupMsg = document.getElementById("signupMsg");
const signupWrapper = document.getElementById("signupWrapper");
const chatbotPanel = document.getElementById("chatbotPanel");
const chatForm = document.getElementById("chatForm");
const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const authHeading = document.getElementById("authHeading");
const loginLink = document.querySelector('nav ul li a[href="/login-page"]');

function getSavedUser() {
  return JSON.parse(localStorage.getItem("lioraUser") || "null");
}

function setSavedUser(user) {
  localStorage.setItem("lioraUser", JSON.stringify(user));
}

function appendChatMessage(text, type = "bot") {
  const message = document.createElement("div");
  message.className = `message ${type}`;
  message.textContent = text;
  chatMessages.appendChild(message);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showChatbot(user) {
  signupWrapper.classList.add("hidden");
  chatbotPanel.classList.remove("hidden");
  authHeading.textContent = `Welcome, ${user.name}`;
  if (loginLink) {
    loginLink.textContent = "Home";
    loginLink.href = "/";
  }
}

function initPage() {
  const storedUser = getSavedUser();
  if (storedUser) {
    showChatbot(storedUser);
  }
}

signupForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  const form = event.currentTarget;
  const name = form.elements.name.value.trim();
  const email = form.elements.email.value.trim();
  const password = form.elements.password.value;

  if (password.length < 8) {
    signupMsg.textContent = "Password must be at least 8 characters.";
    return;
  }

  try {
    const response = await fetch("/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    });
    const data = await response.json();

    if (!response.ok) {
      signupMsg.textContent = data.detail || "Unable to create your account.";
      return;
    }

    const user = { name, email };
    setSavedUser(user);
    signupMsg.textContent = "Account created and signed in. Welcome!";
    form.reset();
    showChatbot(user);
  } catch (error) {
    signupMsg.textContent =
      "Could not reach the server. Start the API and try again.";
  }
});

chatForm.addEventListener("submit", function (event) {
  event.preventDefault();
  const text = chatInput.value.trim();
  if (!text) {
    return;
  }
  appendChatMessage(text, "user");
  chatInput.value = "";

  setTimeout(() => {
    appendChatMessage(
      "Thanks for your question! I can help you compare monthly bills before and after solar installation. For now, save your plan and download the PDF to see the estimate.",
      "bot",
    );
  }, 300);
});

initPage();
