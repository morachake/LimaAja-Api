document.addEventListener("DOMContentLoaded", () => {
  console.log("Dashboard JS loaded")

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

  // Mobile sidebar toggle
  const sidebarToggleMobile = document.querySelector(".cooperative-info .toggle")
  const sidebarMobile = document.querySelector(".sidebar")

  if (sidebarToggleMobile) {
    sidebarToggleMobile.addEventListener("click", () => {
      sidebarMobile.classList.toggle("open")
    })
  }

  // Close sidebar when clicking outside on mobile
  document.addEventListener("click", (event) => {
    const isClickInsideSidebar = sidebarMobile && sidebarMobile.contains(event.target)
    const isClickOnToggle = sidebarToggleMobile && sidebarToggleMobile.contains(event.target)

    if (sidebarMobile && !isClickInsideSidebar && !isClickOnToggle && window.innerWidth < 992) {
      sidebarMobile.classList.remove("open")
    }
  })

  // Handle window resize
  window.addEventListener("resize", () => {
    if (sidebarMobile && window.innerWidth >= 992) {
      sidebarMobile.classList.remove("open")
    }
  })

  // Initialize any charts or interactive elements
  initializeCharts()

  // Profile dropdown toggle
  const profileToggle = document.getElementById("profile-toggle")
  const profileDropdown = document.querySelector(".profile-dropdown")

  if (profileToggle && profileDropdown) {
    profileToggle.addEventListener("click", (e) => {
      e.preventDefault()
      e.stopPropagation()
      profileDropdown.classList.toggle("show")
    })
  }

  // Close dropdowns when clicking outside
  document.addEventListener("click", (event) => {
    if (
      profileDropdown &&
      profileToggle &&
      !profileToggle.contains(event.target) &&
      profileDropdown.classList.contains("show")
    ) {
      profileDropdown.classList.remove("show")
    }
  })

  // Replace the logout modal functionality with this improved version
  // Logout modal functionality
  const logoutBtn = document.getElementById("logout-btn")
  const headerLogoutBtn = document.getElementById("header-logout-btn")
  const logoutModal = document.getElementById("logout-modal")
  const confirmLogoutBtn = document.getElementById("confirm-logout")
  const closeModalBtn = document.querySelector(".logout-modal-close")
  const cancelBtn = document.querySelector(".logout-modal-cancel")
  const loadingSpinner = document.querySelector(".loading-spinner")

  console.log("Logout elements:", {
    logoutBtn,
    headerLogoutBtn,
    logoutModal,
    confirmLogoutBtn,
    closeModalBtn,
    cancelBtn,
  })

  // Show logout modal
  if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault()
      e.stopPropagation()
      console.log("Logout button clicked")
      if (logoutModal) {
        logoutModal.classList.add("show")
        document.body.style.overflow = "hidden" // Prevent scrolling
      }
    })
  }

  if (headerLogoutBtn) {
    headerLogoutBtn.addEventListener("click", (e) => {
      e.preventDefault()
      e.stopPropagation()
      console.log("Header logout button clicked")
      if (logoutModal) {
        logoutModal.classList.add("show")
        document.body.style.overflow = "hidden" // Prevent scrolling

        // Close profile dropdown
        if (profileDropdown && profileDropdown.classList.contains("show")) {
          profileDropdown.classList.remove("show")
        }
      }
    })
  }

  // Close logout modal
  if (closeModalBtn) {
    closeModalBtn.addEventListener("click", () => {
      if (logoutModal) {
        logoutModal.classList.remove("show")
        document.body.style.overflow = "auto" // Re-enable scrolling
      }
    })
  }

  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => {
      if (logoutModal) {
        logoutModal.classList.remove("show")
        document.body.style.overflow = "auto" // Re-enable scrolling
      }
    })
  }

  // Close modal when clicking outside
  if (logoutModal) {
    logoutModal.addEventListener("click", (e) => {
      if (e.target === logoutModal) {
        logoutModal.classList.remove("show")
        document.body.style.overflow = "auto" // Re-enable scrolling
      }
    })
  }

  // Show loading spinner when confirming logout
  if (confirmLogoutBtn) {
    confirmLogoutBtn.addEventListener("click", (e) => {
      e.preventDefault()

      // Show loading spinner
      if (loadingSpinner) {
        loadingSpinner.style.display = "flex"
      }

      // Hide buttons
      const modalFooter = document.querySelector(".logout-modal-footer")
      if (modalFooter) {
        modalFooter.style.display = "none"
      }

      // Redirect after a short delay to show the loading spinner
      setTimeout(() => {
        window.location.href = confirmLogoutBtn.getAttribute("href")
      }, 1000)
    })
  }

  // Handle ESC key to close modals
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      // Close logout modal
      if (logoutModal && logoutModal.classList.contains("show")) {
        logoutModal.classList.remove("show")
        document.body.style.overflow = "auto" // Re-enable scrolling
      }

      // Close profile dropdown
      if (profileDropdown && profileDropdown.classList.contains("show")) {
        profileDropdown.classList.remove("show")
      }
    }
  })
})

function initializeCharts() {
  // This function would initialize any charts using a library like Chart.js
  // For now, it's just a placeholder
  console.log("Charts initialized")
}

