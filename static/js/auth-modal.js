// Auth Modal Functionality
document.addEventListener("DOMContentLoaded", () => {
    // Close modal when clicking outside
    const modalBackdrops = document.querySelectorAll(".modal-backdrop")
  
    modalBackdrops.forEach((backdrop) => {
      backdrop.addEventListener("click", (e) => {
        if (e.target === backdrop) {
          window.location.href = document.querySelector('a[href*="home"]').getAttribute("href")
        }
      })
    })
  
    // Handle escape key to close modal
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        const closeButton = document.querySelector('.modal-content a[href*="home"]')
        if (closeButton) {
          window.location.href = closeButton.getAttribute("href")
        }
      }
    })
  
    // Add animation when modal opens
    const modalContent = document.querySelector(".modal-content")
    if (modalContent) {
      setTimeout(() => {
        modalContent.classList.add("active")
      }, 10)
    }
  
    // Password strength indicator (for registration)
    const passwordInput = document.getElementById("id_password1")
    if (passwordInput) {
      passwordInput.addEventListener("input", function () {
        // Simple password strength check
        const password = this.value
        let strength = 0
  
        if (password.length >= 8) strength += 1
        if (password.match(/[A-Z]/)) strength += 1
        if (password.match(/[0-9]/)) strength += 1
        if (password.match(/[^A-Za-z0-9]/)) strength += 1
  
        // Create or update strength bar if it doesn't exist
        let strengthBar = document.querySelector(".password-strength")
        if (!strengthBar) {
          strengthBar = document.createElement("div")
          strengthBar.className = "password-strength h-1 mt-1 rounded-full"
          passwordInput.parentNode.appendChild(strengthBar)
        }
  
        // Update strength bar
        strengthBar.className = "password-strength h-1 mt-1 rounded-full"
  
        if (strength === 0) {
          strengthBar.classList.add("bg-gray-200", "w-0")
        } else if (strength === 1) {
          strengthBar.classList.add("bg-red-500", "w-1/4")
        } else if (strength === 2) {
          strengthBar.classList.add("bg-yellow-500", "w-2/4")
        } else if (strength === 3) {
          strengthBar.classList.add("bg-blue-500", "w-3/4")
        } else {
          strengthBar.classList.add("bg-green-500", "w-full")
        }
      })
    }
  
    // Form validation
    const forms = document.querySelectorAll("form")
    forms.forEach((form) => {
      form.addEventListener("submit", (e) => {
        const requiredFields = form.querySelectorAll("[required]")
        let isValid = true
  
        requiredFields.forEach((field) => {
          if (!field.value.trim()) {
            isValid = false
            field.classList.add("border-red-500")
  
            // Add error message if not exists
            const errorMsg = field.parentNode.querySelector(".error-message")
            if (!errorMsg) {
              const msg = document.createElement("p")
              msg.className = "text-red-500 text-xs mt-1 error-message"
              msg.textContent = "This field is required"
              field.parentNode.appendChild(msg)
            }
          } else {
            field.classList.remove("border-red-500")
            const errorMsg = field.parentNode.querySelector(".error-message")
            if (errorMsg) errorMsg.remove()
          }
        })
  
        if (!isValid) {
          e.preventDefault()
        }
      })
    })
  
    // Clear cart notifications from auth forms
    const notificationMessages = document.getElementById("notification-messages")
    if (notificationMessages) {
      const cartNotifications = notificationMessages.querySelectorAll("div")
      cartNotifications.forEach((notification) => {
        if (notification.textContent.includes("added to your cart")) {
          notification.remove()
        }
      })
    }
  })
  
  