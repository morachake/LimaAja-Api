// Cart functionality
document.addEventListener("DOMContentLoaded", () => {
  // Handle quantity changes
  const quantityInputs = document.querySelectorAll(".cart-quantity")
  quantityInputs.forEach((input) => {
    input.addEventListener("change", function () {
      const itemId = this.getAttribute("data-item-id")
      const quantity = Number.parseInt(this.value)

      if (quantity > 0) {
        updateCartItem(itemId, quantity)
      } else {
        removeCartItem(itemId)
      }
    })
  })

  // Handle remove buttons
  const removeButtons = document.querySelectorAll(".remove-item")
  removeButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault()
      const itemId = this.getAttribute("data-item-id")
      removeCartItem(itemId)
    })
  })

  // Function to update cart item
  function updateCartItem(itemId, quantity) {
    const formData = new FormData()
    formData.append("action", "update")
    formData.append("quantity", quantity)

    fetch(`/update-cart/${itemId}/`, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          updateCartUI(data)
          // Show notification
          showNotification(`${data.product_name} quantity updated in your cart.`, "success")
        }
      })
      .catch((error) => {
        console.error("Error updating cart:", error)
        showNotification("Failed to update cart. Please try again.", "error")
      })
  }

  // Function to remove cart item
  function removeCartItem(itemId) {
    fetch(`/remove-from-cart/${itemId}/`, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCookie("csrftoken"),
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Remove the item from the DOM
          const itemRow = document.querySelector(`.cart-item[data-item-id="${itemId}"]`)
          if (itemRow) {
            itemRow.remove()
          }

          // Update cart UI
          updateCartUI(data)

          // Show notification
          showNotification(`${data.product_name} removed from your cart.`, "success")

          // Check if cart is empty and show empty state if needed
          const cartItems = document.querySelectorAll(".cart-item")
          if (cartItems.length === 0) {
            showEmptyCart()
          }
        }
      })
      .catch((error) => {
        console.error("Error removing item from cart:", error)
        showNotification("Failed to remove item from cart. Please try again.", "error")
      })
  }

  // Function to update cart UI
  function updateCartUI(data) {
    // Update cart count in header
    const cartCountElements = document.querySelectorAll(".cart-count")
    cartCountElements.forEach((element) => {
      element.textContent = data.cart_count

      // If cart is empty, hide the count
      if (data.cart_count === 0) {
        element.classList.add("hidden")
      } else {
        element.classList.remove("hidden")
      }
    })

    // Update cart total
    const totalElements = document.querySelectorAll(".cart-total")
    totalElements.forEach((element) => {
      element.textContent = formatCurrency(data.cart_total)
    })

    // Update subtotal
    const subtotalElements = document.querySelectorAll(".cart-subtotal")
    subtotalElements.forEach((element) => {
      element.textContent = formatCurrency(data.cart_total)
    })
  }

  // Function to show empty cart state
  function showEmptyCart() {
    const cartTable = document.querySelector(".cart-table")
    const cartSummary = document.querySelector(".cart-summary")
    const emptyCartMessage = document.querySelector(".empty-cart-message")

    if (cartTable) cartTable.classList.add("hidden")
    if (cartSummary) cartSummary.classList.add("hidden")
    if (emptyCartMessage) emptyCartMessage.classList.remove("hidden")
  }

  // Helper function to format currency
  function formatCurrency(amount) {
    return "Rp " + Number.parseFloat(amount).toLocaleString("id-ID")
  }

  // Helper function to get CSRF token
  function getCookie(name) {
    let cookieValue = null
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";")
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim()
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
          break
        }
      }
    }
    return cookieValue
  }

  // Add to cart buttons with AJAX
  const addToCartForms = document.querySelectorAll('form[action*="add-to-cart"]')
  addToCartForms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      e.preventDefault()

      const url = form.action
      const formData = new FormData(form)

      fetch(url, {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": getCookie("csrftoken"),
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            // Update cart count in header
            updateCartUI(data)

            // Show success notification
            showNotification(data.message || `${data.product_name} added to your cart.`, "success")

            // Animate the cart icon
            const cartIcons = document.querySelectorAll(".fa-shopping-cart")
            cartIcons.forEach((icon) => {
              icon.classList.add("cart-added")
              setTimeout(() => {
                icon.classList.remove("cart-added")
              }, 1000)
            })
          } else {
            showNotification(data.error || "Failed to add product to cart.", "error")
          }
        })
        .catch((error) => {
          console.error("Error adding to cart:", error)
          showNotification("Failed to add product to cart. Please try again.", "error")
        })
    })
  })
})

// Function to show notification
function showNotification(message, type = "success") {
  // Create notification container if it doesn't exist
  let notificationContainer = document.getElementById("notification-container")
  if (!notificationContainer) {
    notificationContainer = document.createElement("div")
    notificationContainer.id = "notification-container"
    notificationContainer.className = "fixed top-4 right-4 z-50 w-80"
    document.body.appendChild(notificationContainer)
  }

  // Create notification element
  const notification = document.createElement("div")
  notification.className = `mb-3 p-4 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full ${
    type === "success" ? "bg-green-50 border-l-4 border-green-500" : "bg-red-50 border-l-4 border-red-500"
  }`

  // Add content
  notification.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0 mr-3">
                ${
                  type === "success"
                    ? '<i class="fas fa-check-circle text-green-500"></i>'
                    : '<i class="fas fa-exclamation-circle text-red-500"></i>'
                }
            </div>
            <div class="flex-1">
                <p class="${type === "success" ? "text-green-800" : "text-red-800"}">${message}</p>
            </div>
            <button class="ml-4 text-gray-400 hover:text-gray-600 focus:outline-none">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `

  // Add to container
  notificationContainer.appendChild(notification)

  // Animate in
  setTimeout(() => {
    notification.classList.remove("translate-x-full")
  }, 10)

  // Add close button functionality
  const closeButton = notification.querySelector("button")
  closeButton.addEventListener("click", () => {
    notification.classList.add("translate-x-full")
    setTimeout(() => {
      notification.remove()
    }, 300)
  })

  // Auto remove after 5 seconds
  setTimeout(() => {
    if (notification.parentNode) {
      notification.classList.add("translate-x-full")
      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove()
        }
      }, 300)
    }
  }, 5000)
}

