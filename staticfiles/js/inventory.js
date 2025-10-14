// ===============
// INVENTORY SCRIPT
// ===============

document.addEventListener("DOMContentLoaded", function () {
  // Example interactivity: highlight low stock
  document.querySelectorAll("table tbody tr").forEach(row => {
    const stock = parseInt(row.children[3]?.innerText || "0");
    if (stock < 5) {
      row.classList.add("table-warning");
      row.title = "Low stock alert!";
    }
  });

  // Smooth scroll to top on page load
  window.scrollTo({ top: 0, behavior: "smooth" });
});
