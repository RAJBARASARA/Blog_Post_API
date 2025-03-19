document.addEventListener("DOMContentLoaded", () => {
    const postsContainer = document.getElementById("posts-container");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");

    let currentPage = 1;
    const perPage = 5;
    const API_URL = "http://127.0.0.1:5000/user/posts"; 
    const token = localStorage.getItem("access_token");

    if (!token) {
        alert("You must be logged in to view your posts.");
        window.location.href = "login.html";
        return;
    }

    async function fetchPosts(page) {
        try {
            const response = await fetch(`${API_URL}?page=${page}&per_page=${perPage}`, {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            });

            const data = await response.json();
            postsContainer.innerHTML = "";

            if (response.status !== 200) {
                postsContainer.innerHTML = `<div class="alert alert-info">No posts available.</div>`;
                return;
            }

            data.posts.forEach(post => {
                const postElement = document.createElement("div");
                postElement.classList.add("card");

                postElement.innerHTML = `
                    <div class="post-content">
                        <h3><a href="#" class="post-link" data-slug="${post.slug}">${post.title}</a></h3>
                        <p><small>Posted on ${post.date}</small></p>
                        <p>${post.content.substring(0, 100)}...</p>
                        <a href="#" class="btn btn-primary btn-sm post-link" data-slug="${post.slug}">Read More</a>
                    </div>
                    <div class="post-image">
                        <img src="/static/assets/upload/profile/${post.img_file}" alt="${post.title}">
                    </div>
                `;
                postsContainer.appendChild(postElement);
            });

            prevBtn.disabled = data.current_page === 1;
            nextBtn.disabled = data.current_page >= data.total_pages;

            document.querySelectorAll(".post-link").forEach(link => {
                link.addEventListener("click", function (event) {
                    event.preventDefault();
                    const slug = this.getAttribute("data-slug");
                    window.location.href = `slug.html?slug=${slug}`;
                });
            });

        } catch (error) {
            console.error("Error fetching posts:", error);
            postsContainer.innerHTML = `<div class="alert alert-danger">Failed to load posts.</div>`;
        }
    }

    prevBtn.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            fetchPosts(currentPage);
        }
    });

    nextBtn.addEventListener("click", () => {
        currentPage++;
        fetchPosts(currentPage);
    });

    fetchPosts(currentPage);
});
