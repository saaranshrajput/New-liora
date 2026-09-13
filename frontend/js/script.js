const signupForm = document.getElementById("signupForm");
const signupMsg = document.getElementById("signupMsg");
const signupWrapper = document.getElementById("signupWrapper");
const dashboard = document.getElementById("dashboard");
const authHeading = document.getElementById("authHeading");
const loginLink = document.querySelector('nav ul li a[href="/login-page"]');
const contactLink = document.getElementById("contactLink");
const contactModal = document.getElementById("contactModal");
const contactClose = document.getElementById("contactClose");
const contactForm = document.getElementById("contactForm");
const contactStatus = document.getElementById("contactStatus");

function getSavedUser() {
  return JSON.parse(localStorage.getItem("lioraUser") || "null");
}

function setSavedUser(user) {
  localStorage.setItem("lioraUser", JSON.stringify(user));
}

function finishSignIn(user) {
  setSavedUser(user);
  signupMsg.textContent = "You are signed in. Welcome to Liora!";
  signupForm.reset();
  showDashboard(user);
}

function showDashboard(user) {
  signupWrapper.classList.add("hidden");
  dashboard.classList.remove("hidden");
  const displayName = user.name || user.email.split("@")[0];
  authHeading.textContent = `Welcome, ${displayName}`;
  document.getElementById("dashboardIntro").textContent =
    `${user.email} is ready for a clear solar plan.`;
  const calculation = JSON.parse(
    localStorage.getItem("lioraCalculation") || "null",
  );
  if (calculation) {
    document.getElementById("dashboardUsage").textContent =
      `${calculation.daily} kWh`;
    document.getElementById("dashboardSystem").textContent =
      `${calculation.system} kW`;
    document.getElementById("dashboardSavings").textContent =
      "See recommendation";
  }
  if (loginLink) {
    loginLink.textContent = "Home";
    loginLink.href = "/";
  }
}

function initPage() {
  const storedUser = getSavedUser();
  if (storedUser) {
    showDashboard(storedUser);
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
      if (response.status === 409) {
        const loginResponse = await fetch("/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const loginData = await loginResponse.json();
        if (loginResponse.ok) {
          finishSignIn({
            name: loginData.name || name,
            email: loginData.email || email,
          });
          return;
        }
        signupMsg.textContent =
          "This email is already registered. Use the Login link with your existing password.";
        return;
      }
      signupMsg.textContent = data.detail || "Unable to create your account.";
      return;
    }

    finishSignIn({
      name: data.name || name,
      email: data.email || email,
    });
  } catch (error) {
    signupMsg.textContent =
      "Could not reach the server. Start the API and try again.";
  }
});

initPage();

contactLink.addEventListener("click", (event) => {
  event.preventDefault();
  contactModal.hidden = false;
  contactForm.elements.name.focus();
});

contactClose.addEventListener("click", () => {
  contactModal.hidden = true;
});

contactModal.addEventListener("click", (event) => {
  if (event.target === contactModal) contactModal.hidden = true;
});

contactForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = contactForm.querySelector("button[type='submit']");
  button.disabled = true;
  contactStatus.textContent = "Sending...";
  const formData = new FormData(contactForm);

  try {
    const response = await fetch("/contact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.fromEntries(formData)),
    });
    const data = await response.json();
    if (!response.ok)
      throw new Error(data.detail || "Message could not be sent.");
    contactStatus.textContent = data.message;
    contactForm.reset();
  } catch (error) {
    contactStatus.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});
