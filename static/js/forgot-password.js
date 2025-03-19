document.addEventListener("DOMContentLoaded", function () {
    const forgotPasswordForm = document.getElementById("forgotPasswordForm");
    const emailInput = document.getElementById("forgot-email");
    const forgotMessage = document.getElementById("forgot-message");
    const sendButton = forgotPasswordForm.querySelector("button[type='submit']");

    // Create an error message element for email input
    const emailError = document.createElement("p");
    emailError.className = "error-message";
    emailInput.parentNode.appendChild(emailError);

    forgotPasswordForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        clearErrors();

        if (!validateEmail(emailInput.value.trim())) {
            showFieldError(emailInput, emailError, "Invalid email format.");
            return;
        }

        // Show loading text on button and disable it
        sendButton.innerText = "Processing...";
        sendButton.disabled = true;

        try {
            const response = await fetch("http://127.0.0.1:5000/forgot-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: emailInput.value.trim() }),
            });

            const data = await response.json();

            if (response.ok) {
                showMessage("Password reset email sent!", "black");
            } else {
                if (data.error.toLowerCase().includes("email")) {
                    showFieldError(emailInput, emailError, data.error);
                } else {
                    showMessage(data.error || "Request failed.", "red");
                }
            }
        } catch (error) {
            console.error("Error:", error);
            showMessage("Something went wrong. Try again later.", "red");
        }

        // Reset button after request completes
        sendButton.innerText = "Send";
        sendButton.disabled = false;
    });

    function validateEmail(email) {
        return /^[^@]+@[^@]+\.[^@]+$/.test(email);
    }

    function showMessage(message, color) {
        forgotMessage.innerText = message;
        forgotMessage.style.color = color;
        forgotMessage.style.opacity = "1";

        setTimeout(() => {
            forgotMessage.style.opacity = "0";
        }, 3000);
    }

    function showFieldError(inputField, errorElement, message) {
        inputField.style.border = "2px solid red";
        errorElement.innerText = message;
        errorElement.style.color = "red";
        errorElement.style.opacity = "1";

        setTimeout(() => {
            inputField.style.border = "";
            errorElement.style.opacity = "0";
        }, 5000);
    }

    function clearErrors() {
        emailInput.style.border = "";
        emailError.innerText = "";
    }
});
