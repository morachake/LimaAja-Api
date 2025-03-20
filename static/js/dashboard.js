document.addEventListener("DOMContentLoaded", () => {
  // Sidebar toggle functionality
  const sidebarToggle = document.querySelector(".cooperative-header")
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
  const currentView = new URLSearchParams(window.location.search).get("view")
  const menuLinks = document.querySelectorAll(".sidebar-menu-link")

  menuLinks.forEach((link) => {
    const linkPath = link.getAttribute("href")
    const linkView = new URLSearchParams(linkPath.split("?")[1] || "").get("view")

    if (currentPath === linkPath.split("?")[0]) {
      if (!currentView && !linkView) {
        link.classList.add("active")
      } else if (currentView === linkView) {
        link.classList.add("active")
      }
    }
  })
})

// Dashboard JavaScript

// document.addEventListener("DOMContentLoaded", () => {
//   // Mobile sidebar toggle
//   const sidebarToggle = document.querySelector(".cooperative-info .toggle")
//   const sidebar = document.querySelector(".sidebar")

//   if (sidebarToggle) {
//     sidebarToggle.addEventListener("click", () => {
//       sidebar.classList.toggle("open")
//     })
//   }

//   // Close sidebar when clicking outside on mobile
//   document.addEventListener("click", (event) => {
//     const isClickInsideSidebar = sidebar.contains(event.target)
//     const isClickOnToggle = sidebarToggle && sidebarToggle.contains(event.target)

//     if (!isClickInsideSidebar && !isClickOnToggle && window.innerWidth < 992) {
//       sidebar.classList.remove("open")
//     }
//   })

//   // Handle window resize
//   window.addEventListener("resize", () => {
//     if (window.innerWidth >= 992) {
//       sidebar.classList.remove("open")
//     }
//   })

//   // Initialize any charts or interactive elements
//   initializeCharts()
// })

// function initializeCharts() {
//   // This function would initialize any charts using a library like Chart.js
//   // For now, it's just a placeholder
//   console.log("Charts initialized")
// }


