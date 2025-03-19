document.addEventListener("DOMContentLoaded", function () {
    const contactForm = document.getElementById("contact-form");

    if (!contactForm) {
        console.error("Error: Contact form not found in the DOM.");
        return;
    }

    contactForm.addEventListener("submit", async function (event) {
        event.preventDefault(); // Prevent default form submission

        // Ensure all form elements exist before accessing them
        const nameField = document.getElementById("name");
        const emailField = document.getElementById("email");
        const phoneField = document.getElementById("phone");
        const messageField = document.getElementById("message");

        if (!nameField || !emailField || !phoneField || !messageField) {
            console.error("Error: One or more form fields are missing.");
            return;
        }

        // Collect form data
        const formData = {
            name: nameField.value.trim(),
            email: emailField.value.trim(),
            phone: phoneField.value.trim(),
            message: messageField.value.trim()
        };

        try {
            // Send data to backend
            const response = await fetch("http://127.0.0.1:5000/contact", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(formData)
            });

            const result = response.json();
            console.log('result',result)
            console.log('responce',response)

            if (response.ok) {
                alert(result.message);
                // window.location.href = "home.html"; 
            } else {
                let errorMessages = "";
                for (let key in result.errors) {
                    errorMessages += `${result.errors[key]}\n`;
                }
                alert(errorMessages);
            }
        } catch (error) {
            console.error("Error submitting contact form:", error);
            alert("Something went wrong. Please try again later.");
        }
    });
});
