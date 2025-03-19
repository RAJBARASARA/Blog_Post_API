document.addEventListener("DOMContentLoaded", function () {
    // Get form elements
    const loginForm = document.getElementById("loginForm");
    const loginButton = loginForm.querySelector("button[type='submit']");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const togglePassword = document.getElementById("togglePassword");

    // Create error messages
    const emailError = document.createElement("p");
    emailError.className = "error-message";
    emailInput.parentNode.appendChild(emailError);

    const passwordError = document.createElement("p");
    passwordError.className = "error-message";
    passwordInput.parentNode.appendChild(passwordError);

    // Initially disable the login button
    loginButton.disabled = true;

    function enableInputs() {
        if (emailInput.value.trim() || passwordInput.value.trim()) {
            loginButton.disabled = false;
        } else {
            loginButton.disabled = true;
        }
    }

    emailInput.addEventListener("input", enableInputs);
    passwordInput.addEventListener("input", enableInputs);

    // Toggle password visibility
    togglePassword.addEventListener("click", function () {
        if (passwordInput.type === "password") {
            passwordInput.type = "text";
            togglePassword.innerText = "🙈";
        } else {
            passwordInput.type = "password";
            togglePassword.innerText = "👁️";
        }
    });

    // Handle form submission
    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        clearErrors();
        loginButton.disabled = true;

        try {
            const response = await fetch("http://127.0.0.1:5000/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email: emailInput.value.trim(),
                    password: passwordInput.value.trim(),
                }),
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.setItem("access_token", data.access_token);
                // console.log("Login Success:", data);
                showMessage("Login successful! Redirecting...", "black");
                setTimeout(() => {
                    window.location.replace("../../templates/home.html");
                }, 1500);
            } else {
                if (data.error.toLowerCase().includes("email")) {
                    showFieldError(emailInput, emailError, data.error);
                } else if (data.error.toLowerCase().includes("password")) {
                    showFieldError(passwordInput, passwordError, data.error);
                } else {
                    showMessage(data.error || "Login failed", "red");
                }
            }
        } catch (error) {
            console.error("Error:", error);
            showMessage("Something went wrong! Please try again.", "red");
        }
    });

    function validateEmail(email) {
        return /^[^@]+@[^@]+\.[^@]+$/.test(email);
    }

    function validatePassword(password) {
        return (
            password.length >= 8 && /\d/.test(password) && /[A-Z]/.test(password)
        );
    }

    function showMessage(message, color) {
        const messageElement = document.getElementById("message");
        messageElement.innerText = message;
        messageElement.style.color = color;
        messageElement.style.opacity = "1";

        setTimeout(() => {
            messageElement.style.opacity = "0";
        }, 3000);
    }

    function showFieldError(inputField, errorElement, message) {
        inputField.style.border = "2px solid red";
        errorElement.innerText = message;
        errorElement.style.color = "red";
        errorElement.style.opacity = "1";
        errorElement.style.marginTop = "5px"; // Spacing from input

        setTimeout(() => {
            inputField.style.border = "";
            errorElement.style.opacity = "0";
        }, 5000);
    }

    function clearErrors() {
        emailInput.style.border = "";
        passwordInput.style.border = "";
        emailError.innerText = "";
        passwordError.innerText = "";
    }
});
