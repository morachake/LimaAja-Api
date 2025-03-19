class MultiStepForm {
  constructor() {
    this.currentStep = 1
    this.totalSteps = 3
    this.init()
  }

  init() {
    this.nextBtn = document.getElementById("nextBtn")
    this.prevBtn = document.getElementById("prevBtn")

    if (this.nextBtn && this.prevBtn) {
      this.nextBtn.addEventListener("click", () => this.handleNext())
      this.prevBtn.addEventListener("click", () => this.handlePrev())
    }

    this.updateStep(this.currentStep)
  }

  updateStep(step) {
    // Update form steps visibility
    document.querySelectorAll(".form-step").forEach((el) => {
      el.classList.remove("active")
    })
    document.querySelector(`.form-step[data-step="${step}"]`)?.classList.add("active")

    // Update step indicators
    document.querySelectorAll(".step").forEach((el) => {
      el.classList.remove("active")
    })
    document.querySelector(`.step[data-step="${step}"]`)?.classList.add("active")

    // Update progress dots
    document.querySelectorAll(".dot").forEach((dot, index) => {
      dot.classList.toggle("active", index + 1 <= step)
    })

    // Update navigation buttons
    if (this.prevBtn) {
      this.prevBtn.style.display = step === 1 ? "none" : "block"
    }
    if (this.nextBtn) {
      this.nextBtn.textContent = step === this.totalSteps ? "Submit" : "Next"
    }
  }

  validateCurrentStep() {
    const currentStepElement = document.querySelector(`.form-step[data-step="${this.currentStep}"]`)
    const requiredFields = currentStepElement.querySelectorAll("[required]")
    let isValid = true

    requiredFields.forEach((field) => {
      if (!field.value.trim()) {
        isValid = false
        field.classList.add("error")
        showMessage(`${field.name} is required`, "danger")
      } else {
        field.classList.remove("error")
      }
    })

    return isValid
  }

  handleNext() {
    if (!this.validateCurrentStep()) {
      return
    }

    if (this.currentStep < this.totalSteps) {
      this.currentStep++
      this.updateStep(this.currentStep)
    } else {
      document.getElementById("registrationForm")?.submit()
    }
  }

  handlePrev() {
    if (this.currentStep > 1) {
      this.currentStep--
      this.updateStep(this.currentStep)
    }
  }
}

// Initialize multi-step form if it exists
document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("registrationForm")) {
    new MultiStepForm()
  }
})

// Add this function to handle logout
function handleLogout() {
  // Clear any tokens from localStorage
  localStorage.removeItem("access_token")
  localStorage.removeItem("refresh_token")

  // Redirect to login page
  window.location.href = "/cooperative/login/"
}

// Add event listener to logout buttons
document.addEventListener("DOMContentLoaded", () => {
  const logoutButtons = document.querySelectorAll(".logout-btn, .logout-link")

  logoutButtons.forEach((button) => {
    button.addEventListener("click", (e) => {
      e.preventDefault()
      handleLogout()
    })
  })
})

// Function to display messages (e.g., errors, success)
function showMessage(message, type = "success") {
  const messageDiv = document.createElement("div")
  messageDiv.className = `alert alert-${type}`
  messageDiv.textContent = message

  const formContainer = document.getElementById("registrationForm") // Or any appropriate container
  if (formContainer) {
    formContainer.insertBefore(messageDiv, formContainer.firstChild) // Insert at the top

    // Remove the message after a few seconds
    setTimeout(() => {
      messageDiv.remove()
    }, 5000) // 5 seconds
  } else {
    console.error("Form container not found to display message:", message)
  }
}

