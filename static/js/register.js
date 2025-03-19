document.addEventListener("DOMContentLoaded", function () {
    const registerForm = document.getElementById("registerForm");
    const registerButton = document.querySelector(".register-btn");
    const messageDiv = document.getElementById("message");
    const togglePassword = document.getElementById("togglePassword");

    // Input fields
    const fields = {
        name: document.getElementById("name"),
        dob: document.getElementById("dob"),
        place: document.getElementById("place"),
        address: document.getElementById("address"),
        email: document.getElementById("email"),
        password: document.getElementById("password"),
        image: document.getElementById("image"),
    };

    // Create error message elements dynamically
    const errorElements = {};
    Object.values(fields).forEach(field => {
        const errorElement = document.createElement("p");
        errorElement.className = "error-message";
        errorElement.style.color = "red";
        errorElement.style.fontSize = "14px";
        errorElement.style.marginTop = "5px";
        field.parentNode.appendChild(errorElement);
        errorElements[field.id] = errorElement;
    });

    // Disable submit button initially
    registerButton.disabled = true;

    // Enable submit button if all fields are filled
    function enableSubmitButton() {
        const allFilled = Object.values(fields).every(field => field.value.trim() !== "");
        registerButton.disabled = !allFilled;
    }

    Object.values(fields).forEach(field => field.addEventListener("input", enableSubmitButton));

    // Toggle password visibility
    togglePassword.addEventListener("click", function () {
        if (fields.password.type === "password") {
            fields.password.type = "text";
            togglePassword.innerText = "🙈";
        } else {
            fields.password.type = "password";
            togglePassword.innerText = "👁️";
        }
    });

    // Handle form submission
    registerForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        clearErrors();
        registerButton.disabled = true;
        messageDiv.innerHTML = "Processing...";

        let formData = new FormData(registerForm);

        try {
            const response = await fetch("http://127.0.0.1:5000/register", {
                method: "POST",
                body: formData
            });

            const data = await response.json();
            messageDiv.innerHTML = "";

            if (response.ok && data.status) {
                showMessage("Registration successful! Redirecting...", "green");

                // Reset form & redirect after a delay
                setTimeout(() => {
                    registerForm.reset();
                    registerButton.disabled = true;
                    messageDiv.innerHTML = "";
                    window.location.href = "login.html";  // Redirect to login page
                }, 2000);
            } else {
                if (data.errors) {
                    for (let key in data.errors) {
                        showFieldError(fields[key], errorElements[key], data.errors[key]);
                    }
                } else {
                    showMessage(data.error || "Registration failed!", "red");
                }
            }
        } catch (error) {
            console.error("Error:", error);
            showMessage("Something went wrong! Please try again.", "red");
        } finally {
            registerButton.disabled = false;
        }
    });

    function showMessage(message, color) {
        messageDiv.innerHTML = `<p style="color:${color}; font-weight:bold;">${message}</p>`;
        setTimeout(() => {
            messageDiv.innerHTML = "";
        }, 3000);
    }

    function showFieldError(inputField, errorElement, message) {
        inputField.style.border = "2px solid red";
        errorElement.innerText = message;
        errorElement.style.opacity = "1";

        setTimeout(() => {
            inputField.style.border = "";
            errorElement.style.opacity = "0";
        }, 5000);
    }

    function clearErrors() {
        Object.values(fields).forEach(field => {
            field.style.border = "";
            errorElements[field.id].innerText = "";
        });
    }
});
