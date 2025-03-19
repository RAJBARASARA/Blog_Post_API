document.addEventListener("DOMContentLoaded", function () {
    // Get form elements
    const resetForm = document.getElementById("resetPasswordForm");
    const resetButton = resetForm.querySelector("button[type='submit']");
    const newPasswordInput = document.getElementById("new_password");
    const confirmPasswordInput = document.getElementById("confirm_password");
    const toggleNewPassword = document.getElementById("toggleNewPassword");
    const toggleConfirmPassword = document.getElementById("toggleConfirmPassword");

    // Create error messages and insert below input fields
    const newPasswordError = document.createElement("p");
    newPasswordError.className = "error-message";
    newPasswordInput.closest(".input-group").appendChild(newPasswordError);

    const confirmPasswordError = document.createElement("p");
    confirmPasswordError.className = "error-message";
    confirmPasswordInput.closest(".input-group").appendChild(confirmPasswordError);

    // Initially disable the reset button
    resetButton.disabled = true;

    function enableButton() {
        if (newPasswordInput.value.trim() && confirmPasswordInput.value.trim()) {
            resetButton.disabled = false;
        } else {
            resetButton.disabled = true;
        }
    }

    newPasswordInput.addEventListener("input", enableButton);
    confirmPasswordInput.addEventListener("input", enableButton);

    // Toggle password visibility
    function togglePasswordVisibility(inputField, toggleButton) {
        toggleButton.addEventListener("click", function () {
            if (inputField.type === "password") {
                inputField.type = "text";
                toggleButton.innerText = "🙈";
            } else {
                inputField.type = "password";
                toggleButton.innerText = "👁️";
            }
        });
    }

    togglePasswordVisibility(newPasswordInput, toggleNewPassword);
    togglePasswordVisibility(confirmPasswordInput, toggleConfirmPassword);

    // Extract token from query params
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get("token");

    if (!token) {
        showMessage("Invalid reset link. Please try again.", "red");
        return;
    }

    // Handle form submission
    resetForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        resetButton.disabled = true;

        const newPassword = newPasswordInput.value.trim();
        const confirmPassword = confirmPasswordInput.value.trim();

        // Client-side validation
        if (!validatePassword(newPassword)) {
            showFieldError(newPasswordInput, newPasswordError, "Password must be at least 8 characters, include a number and an uppercase letter.");
            resetButton.disabled = false;
            return;
        }

        if (newPassword !== confirmPassword) {
            showFieldError(confirmPasswordInput, confirmPasswordError, "Passwords do not match.");
            resetButton.disabled = false;
            return;
        }

        try {
            const response = await fetch(`http://127.0.0.1:5000/reset-password/${token}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ new_password: newPassword, confirm_password: confirmPassword }),
            });

            const data = await response.json();

            if (response.ok) {
                showMessage("Password reset successful! Redirecting to login...", "green");
                setTimeout(() => (window.location.href = "./login.html"), 2000);
            } else {
                if (data.error.toLowerCase().includes("password")) {
                    showFieldError(newPasswordInput, newPasswordError, data.error);
                } else {
                    showMessage(data.error || "Password reset failed", "red");
                }
                resetButton.disabled = false;
            }
        } catch (error) {
            console.error("Error:", error);
            showMessage("Something went wrong! Please try again.", "red");
            resetButton.disabled = false;
        }
    });

    function validatePassword(password) {
        return password.length >= 8 && /\d/.test(password) && /[A-Z]/.test(password);
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
        errorElement.innerText = message;
        errorElement.style.color = "red";
        errorElement.style.opacity = "1";
        errorElement.style.marginTop = "5px"; // Spacing from input

        inputField.style.border = "2px solid red";

        setTimeout(() => {
            inputField.style.border = "";
            errorElement.innerText = "";
            errorElement.style.opacity = "0";
        }, 5000);
    }

    function clearErrors() {
        newPasswordInput.style.border = "";
        confirmPasswordInput.style.border = "";
        newPasswordError.innerText = "";
        confirmPasswordError.innerText = "";
    }
});
