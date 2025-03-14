// Utility functions
function showMessage(message, type = "info") {
    const alertDiv = document.createElement("div")
    alertDiv.className = `alert alert-${type}`
    alertDiv.textContent = message
  
    const container = document.querySelector(".container") || document.body
    container.insertBefore(alertDiv, container.firstChild)
  
    setTimeout(() => {
      alertDiv.remove()
    }, 5000)
  }
  
  // Form validation
  function validateForm(form) {
    const requiredFields = form.querySelectorAll("[required]")
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
  
  // Event listeners
  document.addEventListener("DOMContentLoaded", () => {
    // Handle form submissions
    const forms = document.querySelectorAll("form")
    forms.forEach((form) => {
      form.addEventListener("submit", (e) => {
        if (!validateForm(form)) {
          e.preventDefault()
        }
      })
    })
  
    // Handle input validation on blur
    const inputs = document.querySelectorAll(".form-control")
    inputs.forEach((input) => {
      input.addEventListener("blur", () => {
        if (input.hasAttribute("required") && !input.value.trim()) {
          input.classList.add("error")
        } else {
          input.classList.remove("error")
        }
      })
    })
  })
  
  