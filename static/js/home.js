document.addEventListener("DOMContentLoaded", function () {
    const postContainer = document.querySelector(".post.container");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");
    const pageNumbers = document.getElementById("pageNumbers");
    const navButtons = document.getElementById("nav-buttons");
    const searchInput = document.getElementById("search-input");
    const searchBtn = document.getElementById("search-btn");

    let currentPage = 1;
    const perPage = 4;
    const apiUrl = "http://127.0.0.1:5000/post";

    function updateNavButtons() {
        const accessToken = localStorage.getItem("access_token");
        const protectedLinks = document.querySelectorAll(".protected-link");

        if (accessToken) {
            navButtons.innerHTML = `
                <a href="#" class="logout" id="logoutBtn">Logout</a>
            `;

            // Show protected links (Post & Dashboard)
            protectedLinks.forEach(link => link.style.display = "inline-block");

            document.getElementById("logoutBtn").addEventListener("click", function (event) {
                event.preventDefault();
                localStorage.removeItem("access_token");
                updateNavButtons();
            });
        } else {
            navButtons.innerHTML = `
                <a href="./register.html" class="login">Sign Up</a>
                <a href="./login.html" class="login">Login</a>
            `;
            
            // Hide protected links when not logged in
            protectedLinks.forEach(link => link.style.display = "none");
        }
    }

    async function fetchPosts(page = 1, search = "") {
        try {
            let url = new URL(apiUrl);
            url.searchParams.append("page", page);
            url.searchParams.append("per_page", perPage);
            if (search.trim() !== "") {
                url.searchParams.append("search", search);
            }

            const response = await fetch(url.toString());
            const data = await response.json();

            if (data.status) {
                displayPosts(data.posts);
                updatePagination(data.current_page, data.total_pages, search);
            } else {
                console.error("Error fetching posts:", data.error);
            }
        } catch (error) {
            console.error("Error:", error);
        }
    }

    function displayPosts(posts) {
        postContainer.innerHTML = "";
        if (posts.length === 0) {
            postContainer.innerHTML = `<p style="color: white;">No posts found.</p>`;
            return;
        }

        posts.forEach(post => {
            const postHTML = `
                <div class="post-box">
                    <div class="content">
                        <img src="../static/assets/upload/profile/${post.img_file}" alt="${post.title}" class="post-img">
                        <h2 class="category">${post.slug || "General"}</h2>
                        <a href="./slug.html?slug=${post.slug}" class="post-title">${post.title}</a>
                        <span class="post-date">${post.date}</span>
                        <p class="post-description">${post.content.substring(0, 100)}...</p>
                    </div>
                    <div class="profile">
                        <img src="../static/assets/img/logo.png" alt="" class="profile-img">
                        <span class="profile-name">${post.author}</span>
                    </div>
                </div>
            `;
            postContainer.innerHTML += postHTML;
        });
    }

    function updatePagination(current, total, search) {
        currentPage = current;
    
        // Hide pagination if there are no posts
        if (total <= 1) {
            pageNumbers.innerHTML = "";
            prevBtn.style.display = "none";
            nextBtn.style.display = "none";
            return;
        } else {
            prevBtn.style.display = "inline-block";
            nextBtn.style.display = "inline-block";
        }
    
        prevBtn.disabled = currentPage === 1;
        nextBtn.disabled = currentPage === total;
    
        let paginationHTML = "";
    
        for (let i = 1; i <= total; i++) {
            paginationHTML += `<button class="page-btn ${i === current ? 'active' : ''}" data-page="${i}">${i}</button>`;
        }
    
        pageNumbers.innerHTML = paginationHTML;
    
        document.querySelectorAll(".page-btn").forEach(btn => {
            btn.addEventListener("click", function () {
                fetchPosts(parseInt(this.dataset.page), search);
            });
        });
    }

    prevBtn.addEventListener("click", function () {
        if (currentPage > 1) fetchPosts(currentPage - 1, searchInput.value.trim());
    });

    nextBtn.addEventListener("click", function () {
        fetchPosts(currentPage + 1, searchInput.value.trim());
    });

    searchBtn.addEventListener("click", function () {
        fetchPosts(1, searchInput.value.trim());
    });

    searchInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            searchBtn.click();
        }
    });

    updateNavButtons();
    fetchPosts();
});
