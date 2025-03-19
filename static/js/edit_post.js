// Get Post ID from URL
const urlParams = new URLSearchParams(window.location.search);
const postId = urlParams.get("id");

if (!postId) {
    document.getElementById("message").innerHTML = "<p style='color: red;'>Post ID not found!</p>";
} else {
    // Fetch post details and fill the form
    fetch(`http://localhost:5000/edit/${postId}`, {
        method: "GET",
        headers: { "Authorization": `Bearer ${localStorage.getItem("access_token")}` }
    })
    .then(response => response.json())
    .then(data => {
        if (data.post) {
            document.getElementById("postId").value = data.post.id;
            document.getElementById("title").value = data.post.title;
            document.getElementById("slug").value = data.post.slug;
            document.getElementById("content").value = data.post.content;

            if (data.post.img_file) {
                document.getElementById("currentImage").src = `../static/assets/upload/profile/${data.post.img_file}`;
            } else {
                document.getElementById("imageContainer").style.display = "none";
            }
        } else {
            document.getElementById("message").innerHTML = `<p style='color: red;'>${data.error}</p>`;
        }
    })
    .catch(error => {
        console.error("Error fetching post:", error);
        document.getElementById("message").innerHTML = "<p style='color: red;'>Failed to load post data!</p>";
    });
}

// Handle form submission
document.getElementById("editPostForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData();
    formData.append("title", document.getElementById("title").value);
    formData.append("content", document.getElementById("content").value);

    const imgFile = document.getElementById("img_file").files[0];
    if (imgFile) formData.append("img_file", imgFile);

    try {
        const response = await fetch(`http://localhost:5000/edit/${postId}`, {
            method: "PUT",
            headers: { "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById("message").innerHTML = `<p style='color: green;'>${data.message}</p>`;
            setTimeout(() => {
                window.location.href = "dashboard.html";
            }, 2000);
        } else {
            document.getElementById("message").innerHTML = `<p style='color: red;'>${data.error}</p>`;
        }
    } catch (error) {
        console.error("Error updating post:", error);
        document.getElementById("message").innerHTML = "<p style='color: red;'>Error updating post!</p>";
    }
});

