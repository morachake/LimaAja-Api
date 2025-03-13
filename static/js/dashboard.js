document.addEventListener("DOMContentLoaded", () => {
    // Sidebar toggle functionality
    const sidebarToggle = document.getElementById("sidebar-toggle")
    const sidebar = document.getElementById("sidebar")
    const mainContent = document.getElementById("main-content")
    const mobileMenuToggle = document.getElementById("mobile-menu-toggle")
    const sidebarOverlay = document.getElementById("sidebar-overlay")
  
    // Check if sidebar state is stored in localStorage
    const sidebarCollapsed = localStorage.getItem("sidebarCollapsed") === "true"
  
    // Initialize sidebar state
    if (sidebarCollapsed) {
      sidebar.classList.add("collapsed")
      mainContent.classList.add("expanded")
    }
  
    // Toggle sidebar on button click
    if (sidebarToggle) {
      sidebarToggle.addEventListener("click", () => {
        sidebar.classList.toggle("collapsed")
        mainContent.classList.toggle("expanded")
  
        // Store sidebar state in localStorage
        localStorage.setItem("sidebarCollapsed", sidebar.classList.contains("collapsed"))
      })
    }
  
    // Mobile menu toggle
    if (mobileMenuToggle) {
      mobileMenuToggle.addEventListener("click", () => {
        sidebar.classList.add("mobile-open")
        sidebarOverlay.classList.add("active")
      })
    }
  
    // Close sidebar when clicking on overlay
    if (sidebarOverlay) {
      sidebarOverlay.addEventListener("click", () => {
        sidebar.classList.remove("mobile-open")
        sidebarOverlay.classList.remove("active")
      })
    }
  
    // Set active menu item based on current page
    const currentPath = window.location.pathname
    const menuLinks = document.querySelectorAll(".sidebar-menu-link")
  
    menuLinks.forEach((link) => {
      const linkPath = link.getAttribute("href")
      if (currentPath === linkPath || (currentPath.startsWith(linkPath) && linkPath !== "/cooperative/")) {
        link.classList.add("active")
      }
    })
  })
  
  