(function () {
  const form = document.getElementById("loginForm");
  const emailInput = document.getElementById("email");
  const pwInput = document.getElementById("password");
  const emailError = document.getElementById("emailError");
  const pwError = document.getElementById("passwordError");
  const submitBtn = document.getElementById("submitBtn");
  const rememberInput = document.getElementById("remember");
  const statusBanner = document.getElementById("statusBanner");
  const togglePw = document.getElementById("togglePw");
  const forgotForm = document.getElementById("forgotPasswordForm");
  const resetForm = document.getElementById("resetPasswordForm");
  const socialDivider = document.getElementById("socialDivider");
  const socialRow = document.getElementById("socialRow");
  const appleBtn = document.getElementById("appleBtn");
  const googleButtonContainer = document.getElementById("googleButtonContainer");
  const authHeading = document.querySelector(".auth-card h1");
  const authSub = document.querySelector(".auth-sub");
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const resetToken = new URLSearchParams(window.location.hash.slice(1)).get("reset_token");
  const apiBase =
    window.location.origin && window.location.origin !== "null"
      ? window.location.origin
      : "http://127.0.0.1:8000";

  async function readJsonResponse(response) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  function setSavedUser(user, remember = true) {
    localStorage.removeItem("lioraUser");
    sessionStorage.removeItem("lioraUser");
    const storage = remember ? localStorage : sessionStorage;
    storage.setItem("lioraUser", JSON.stringify(user));
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

  function setMode(mode) {
    const isLogin = mode === "login";
    const isForgot = mode === "forgot";
    const socialEnabled = socialRow.dataset.enabled === "true";
    form.classList.toggle("hidden", !isLogin);
    forgotForm.classList.toggle("hidden", !isForgot);
    resetForm.classList.toggle("hidden", mode !== "reset");
    socialDivider.classList.toggle("hidden", !isLogin || !socialEnabled);
    socialRow.classList.toggle("hidden", !isLogin || !socialEnabled);
    authHeading.textContent =
      mode === "reset" ? "Choose a new password" :
      isForgot ? "Reset your password" : "Welcome back";
    authSub.textContent =
      mode === "reset" ? "Choose a new password for your Liora account." :
      isForgot ? "We’ll email you a secure link to reset your password." :
      "Sign in to keep tracking your energy, your way.";
    clearStatus();
  }

  function createNonce() {
    const bytes = crypto.getRandomValues(new Uint8Array(32));
    return btoa(String.fromCharCode(...bytes))
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");
  }

  async function completeOAuth(provider, identityToken, nonce) {
    const response = await fetch(`${apiBase}/auth/${provider}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identity_token: identityToken, nonce }),
    });
    const data = await readJsonResponse(response);
    if (!response.ok) {
      throw new Error(data?.detail || "Social sign-in could not be completed.");
    }
    setSavedUser({ name: data.name, email: data.email }, rememberInput.checked);
    window.location.href = "/";
  }

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = src;
      script.async = true;
      script.onload = resolve;
      script.onerror = () => reject(new Error("Sign-in provider could not be loaded."));
      document.head.appendChild(script);
    });
  }

  async function configureSocialSignIn() {
    try {
      const response = await fetch(`${apiBase}/auth/config`);
      if (!response.ok) return;
      const config = await response.json();

      if (config.google_client_id) {
        googleButtonContainer.classList.remove("hidden");
        try {
          await loadScript("https://accounts.google.com/gsi/client");
          const nonce = createNonce();
          window.google.accounts.id.initialize({
            client_id: config.google_client_id,
            nonce,
            callback: ({ credential }) => {
              completeOAuth("google", credential, nonce).catch((error) => {
                setStatus(error.message, "error");
              });
            },
          });
          window.google.accounts.id.renderButton(googleButtonContainer, {
            theme: "filled_black",
            size: "large",
            text: "continue_with",
            shape: "rectangular",
            width: Math.max(120, document.querySelector(".auth-card").clientWidth - 60),
          });
          socialRow.dataset.enabled = "true";
        } catch (error) {
          googleButtonContainer.classList.add("hidden");
          setStatus(error.message, "error");
        }
      }

      if (config.apple_client_id) {
        appleBtn.classList.remove("hidden");
        try {
          await loadScript(
            "https://appleid.cdn-apple.com/appleauth/static/jsapi/appleid/1/en_US/appleid.auth.js",
          );
          socialRow.dataset.enabled = "true";
          appleBtn.addEventListener("click", async () => {
            const nonce = createNonce();
            try {
              window.AppleID.auth.init({
                clientId: config.apple_client_id,
                scope: "name email",
                redirectURI: `${window.location.origin}/login-page`,
                usePopup: true,
                nonce,
              });
              const result = await window.AppleID.auth.signIn();
              await completeOAuth("apple", result.authorization.id_token, nonce);
            } catch (error) {
              setStatus(error.message || "Apple sign-in could not be completed.", "error");
            }
          });
        } catch (error) {
          appleBtn.classList.add("hidden");
          setStatus(error.message, "error");
        }
      }

      if (
        !googleButtonContainer.classList.contains("hidden") ||
        !appleBtn.classList.contains("hidden")
      ) {
        socialRow.dataset.enabled = "true";
      }
      setMode(resetToken ? "reset" : "login");
    } catch {
      setMode(resetToken ? "reset" : "login");
    }
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
      setSavedUser(user, rememberInput.checked);
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
    setMode("forgot");
  });

  document.getElementById("backToLoginFromForgot").addEventListener("click", (event) => {
    event.preventDefault();
    setMode("login");
  });
  document.getElementById("backToLoginFromReset").addEventListener("click", (event) => {
    event.preventDefault();
    setMode("login");
    window.history.replaceState({}, "", "/login-page");
  });

  forgotForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("resetEmail").value.trim();
    if (!emailPattern.test(email)) {
      setStatus("Enter a valid email address.", "error");
      return;
    }
    const button = document.getElementById("forgotSubmitBtn");
    button.disabled = true;
    try {
      const response = await fetch(`${apiBase}/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await readJsonResponse(response);
      if (!response.ok) {
        setStatus(data?.detail || `Could not request a reset (HTTP ${response.status}).`, "error");
        return;
      }
      setStatus(data.message, "success");
    } catch (error) {
      setStatus(`Could not reach the server. (${error.message})`, "error");
    } finally {
      button.disabled = false;
    }
  });

  resetForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const password = document.getElementById("newPassword").value;
    const confirmation = document.getElementById("confirmPassword").value;
    if (!resetToken) {
      setStatus("This reset link is invalid. Request a new one.", "error");
      return;
    }
    if (password.length < 8) {
      setStatus("Password must be at least 8 characters.", "error");
      return;
    }
    if (password !== confirmation) {
      setStatus("The passwords do not match.", "error");
      return;
    }
    const button = document.getElementById("resetSubmitBtn");
    button.disabled = true;
    try {
      const response = await fetch(`${apiBase}/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: resetToken, password }),
      });
      const data = await readJsonResponse(response);
      if (!response.ok) {
        setStatus(data?.detail || `Could not reset password (HTTP ${response.status}).`, "error");
        return;
      }
      setStatus(data.message, "success");
      resetForm.reset();
      window.history.replaceState({}, "", "/login-page");
      window.setTimeout(() => setMode("login"), 2000);
    } catch (error) {
      setStatus(`Could not reach the server. (${error.message})`, "error");
    } finally {
      button.disabled = false;
    }
  });

  configureSocialSignIn();
})();
