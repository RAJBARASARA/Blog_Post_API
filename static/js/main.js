// (Enables Menu Toggle)
document.addEventListener("DOMContentLoaded", function () {
  const menu = document.querySelector(".menu");
  const hamburger = document.querySelector(".hamburger");

  hamburger.addEventListener("click", () => {
    menu.classList.toggle("active");
  });
});

// Pagination functionality
document.addEventListener("DOMContentLoaded", function () {
  const postsPerPage = 3;
  const posts = document.querySelectorAll(".post-box");
  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");
  const pageNumbers = document.getElementById("pageNumbers");
  let currentPage = 1;
  const totalPages = Math.ceil(posts.length / postsPerPage);

  function showPage(page) {
    currentPage = page;
    posts.forEach((post, index) => {
      post.style.display =
        index >= (page - 1) * postsPerPage && index < page * postsPerPage
          ? "block"
          : "none";
    });
    updatePaginationControls();
  }

  function updatePaginationControls() {
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;
    pageNumbers.innerHTML = `Page ${currentPage} of ${totalPages}`;
  }

  prevBtn.addEventListener("click", function () {
    if (currentPage > 1) {
      showPage(currentPage - 1);
    }
  });

  nextBtn.addEventListener("click", function () {
    if (currentPage < totalPages) {
      showPage(currentPage + 1);
    }
  });

  showPage(1);
});
