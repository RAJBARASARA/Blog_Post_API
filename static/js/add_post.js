document.getElementById("addPostForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const formData = new FormData();
    formData.append("title", document.getElementById("title").value.trim());
    formData.append("content", document.getElementById("content").value.trim());
    formData.append("img_file", document.getElementById("img_file").files[0]);

    const token = localStorage.getItem("access_token");

    try {
        const response = await fetch("http://127.0.0.1:5000/add", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`
            },
            body: formData
        });

        const result = await response.json();

        const messageBox = document.getElementById("message");

        if (result.status) {
            messageBox.innerHTML = `<p style="color: green;">Post added successfully! Redirecting...</p>`;
            window.location.href = "dashboard.html"; 
        } else {
            messageBox.innerHTML = `<p style="color: red;">${result.error}</p>`;
        }

    } catch (error) {
        console.error("Error:", error);
        document.getElementById("message").innerHTML = `<p style="color: red;">An error occurred!</p>`;
    }
});
