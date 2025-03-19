document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "login.html";
    } else {
        fetchUserName(token);
        fetchUserPosts(1, "");
    }
});

let currentPage = 1;
const perPage = 4;

// Fetch and display total post count
async function fetchUserPosts(page = 1, search = "") {
    const token = localStorage.getItem("access_token");
    let url = new URL("http://127.0.0.1:5000/user/posts");

    if (page && page > 0) {
        url.searchParams.append("page", page);
    }
    if (perPage && perPage > 0) {
        url.searchParams.append("per_page", perPage);
    }
    if (search.trim() !== "") {
        url.searchParams.append("search", search);
    }

    try {
        const response = await fetch(url.toString(), {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (response.status === 401) {
            localStorage.removeItem("access_token");
            window.location.href = "login.html";
            return [];
        }

        const data = await response.json();
        if (data.status) {
            displayPosts(data.posts);
            updatePagination(data.current_page, data.total_pages);
            document.getElementById("total-posts").textContent = data.total_posts; 
            return data.posts; // Return posts for filtering
        } else {
            console.error("Error fetching posts:", data.error);
            return [];
        }
    } catch (error) {
        console.error("Error:", error);
        return [];
    }
}

function displayPosts(posts) {
    const tableBody = document.getElementById("posts-table-body");
    tableBody.innerHTML = ""; // Clear previous posts

    if (posts.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="4" style="text-align:center;">No posts found</td></tr>`;
        return;
    }

    posts.forEach((post, index) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${post.title}</td>
            <td>${post.date}</td>
            <td class="actions">
                <button class="btn-edit" onclick="editPost(${post.id})"><i class='bx bx-edit'></i></button>
                <button class="btn-delete" onclick="deletePost(${post.id})"><i class='bx bx-trash'></i></button>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

function updatePagination(current, total) {
    const paginationContainer = document.querySelector(".pagination");

    // If no pages or no posts, hide pagination
    if (total === 0 || total === 1) {
        paginationContainer.innerHTML = "";
        paginationContainer.style.display = "none"; // Hide pagination container
        return;
    } else {
        paginationContainer.style.display = "flex"; // Show pagination when needed
    }

    paginationContainer.innerHTML = "";

    // Prev Button (Hidden if on the first page)
    if (current > 1) {
        paginationContainer.innerHTML += `<button class="page-btn" data-page="${current - 1}">Prev</button>`;
    }

    // Page Numbers
    for (let i = 1; i <= total; i++) {
        paginationContainer.innerHTML += `<button class="page-btn ${i === current ? 'active' : ''}" data-page="${i}">${i}</button>`;
    }

    // Next Button (Hidden if on the last page)
    if (current < total) {
        paginationContainer.innerHTML += `<button class="page-btn" data-page="${current + 1}">Next</button>`;
    }
}
document.querySelector(".pagination").addEventListener("click", (event) => {
    if (event.target.classList.contains("page-btn")) {
        fetchUserPosts(parseInt(event.target.dataset.page), document.getElementById("search-input").value);
    }
});

document.getElementById("search-input").addEventListener("input", function () {
    fetchUserPosts(1, this.value.trim());
});

// Function to Delete a Post and Update Total Count
function deletePost(postId) {
    const token = localStorage.getItem("access_token");

    fetch(`http://127.0.0.1:5000/delete/${postId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status) {
            alert("Post deleted successfully!");
            fetchUserPosts(currentPage, document.getElementById("search-input").value);
        } else {
            alert(data.error);
        }
    })
    .catch(error => console.error("Error deleting post:", error));
}
// Fetch and display user name
function fetchUserName(token) {
    fetch("http://127.0.0.1:5000/profile", {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status && data.user) {
            document.getElementById("user-name").textContent = `Welcome, ${data.user.name}`;
        } else {
            console.error("Error fetching user details:", data.error);
        }
    })
    .catch(error => console.error("Error:", error));
}
// Function to Redirect for Editing Post
function editPost(postId) {
    window.location.href = `edit_post.html?id=${postId}`;
}

// Logout Functionality
document.getElementById("logout").addEventListener("click", (e) => {
    e.preventDefault();
    localStorage.removeItem("access_token");
    window.location.href = "login.html";
});
