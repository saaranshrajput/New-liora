(function () {
  const form = document.getElementById("loginForm");
  const emailInput = document.getElementById("email");
  const pwInput = document.getElementById("password");
  const emailError = document.getElementById("emailError");
  const pwError = document.getElementById("passwordError");
  const submitBtn = document.getElementById("submitBtn");
  const statusBanner = document.getElementById("statusBanner");
  const togglePw = document.getElementById("togglePw");
  const dividerRow = document.querySelector(".divider-row");
  const socialRow = document.querySelector(".social-row");
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const apiBase =
    window.location.origin && window.location.origin !== "null"
      ? window.location.origin
      : "http://127.0.0.1:8000";

  function getSavedUser() {
    return JSON.parse(localStorage.getItem("lioraUser") || "null");
  }

  function setSavedUser(user) {
    localStorage.setItem("lioraUser", JSON.stringify(user));
  }

  function setStatus(message, type) {
    statusBanner.textContent = message;
    statusBanner.className =
      "status-banner show" + (type === "error" ? " error" : "");
  }

  function clearStatus() {
    statusBanner.className = "status-banner";
    statusBanner.textContent = "";
  }

  function validateEmail() {
    const valid = emailPattern.test(emailInput.value.trim());
    emailInput.classList.toggle("err", !valid);
    emailError.classList.toggle("show", !valid);
    return valid;
  }

  function validatePassword() {
    const valid = pwInput.value.length > 0;
    pwInput.classList.toggle("err", !valid);
    pwError.classList.toggle("show", !valid);
    return valid;
  }

  emailInput.addEventListener("blur", validateEmail);
  pwInput.addEventListener("blur", validatePassword);
  emailInput.addEventListener("input", () => {
    if (emailInput.classList.contains("err")) validateEmail();
  });
  pwInput.addEventListener("input", () => {
    if (pwInput.classList.contains("err")) validatePassword();
  });

  togglePw.addEventListener("click", () => {
    const isPw = pwInput.type === "password";
    pwInput.type = isPw ? "text" : "password";
    togglePw.textContent = isPw ? "Hide" : "Show";
    togglePw.setAttribute(
      "aria-label",
      isPw ? "Hide password" : "Show password",
    );
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearStatus();

    if (!validateEmail() || !validatePassword()) {
      setStatus(
        "Please fix the highlighted fields before continuing.",
        "error",
      );
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span>Signing in…';

    try {
      const response = await fetch(`${apiBase}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: emailInput.value.trim(),
          password: pwInput.value,
        }),
      });

      let data = null;
      try {
        data = await response.json();
      } catch (jsonError) {
        data = null;
      }

      if (!response.ok) {
        setStatus(
          data?.detail ||
            data?.message ||
            "Unable to sign in. Please try again.",
          "error",
        );
        return;
      }

      const user = {
        name: data.name,
        email: data.email || emailInput.value.trim(),
      };
      setSavedUser(user);
      window.location.href = "/";
    } catch (error) {
      setStatus(
        `Could not reach the server. Start the API and try again. (${error.message})`,
        "error",
      );
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Sign in";
    }
  });

  document.getElementById("forgotLink").addEventListener("click", (event) => {
    event.preventDefault();
    setStatus("Password reset is not available yet.", "error");
  });

  ["appleBtn", "googleBtn"].forEach((id) => {
    document.getElementById(id).addEventListener("click", () => {
      setStatus("This option is not available yet.", "error");
    });
  });
})();
