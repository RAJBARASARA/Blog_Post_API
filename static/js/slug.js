document.addEventListener("DOMContentLoaded", async () => {
    const params = new URLSearchParams(window.location.search);
    const slug = params.get("slug");

    if (!slug) {
        alert("Invalid post.");
        window.location.href = "index.html";
        return;
    }

    const API_URL = `http://127.0.0.1:5000/post/${slug}`;
    const token = localStorage.getItem("access_token");

    try {
        const response = await fetch(API_URL, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        const data = await response.json();

        if (!data.status) {
            alert("Post not found.");
            window.location.href = "index.html";
            return;
        }

        const post = data.post[0];

        document.getElementById("post-title").textContent = post.title;
        document.getElementById("post-date").innerHTML = `<small>Posted on ${post.date}</small>`;
        document.getElementById("post-body").textContent = post.content;
        document.getElementById("post-image").src = `/static/assets/upload/profile/${post.img_file}`;
        document.getElementById("post-image").alt = post.title;
    } catch (error) {
        console.error("Error fetching post:", error);
        alert("Failed to load post."); 
        window.location.href = "index.html";
    }
});
