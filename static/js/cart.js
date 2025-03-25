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

  // Handle quantity update buttons
  const updateForms = document.querySelectorAll(".update-cart-form")
  updateForms.forEach((form) => {
    form.addEventListener("submit", function (e) {
      e.preventDefault()
      const itemId = this.closest(".cart-item").getAttribute("data-item-id")
      const action = e.submitter.value

      updateCartItemQuantity(itemId, action)
    })
  })

  // Function to update cart item quantity
  function updateCartItemQuantity(itemId, action) {
    const formData = new FormData()
    formData.append("action", action)

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
          // Update the quantity display
          const cartItem = document.querySelector(`.cart-item[data-item-id="${itemId}"]`)
          if (cartItem) {
            const quantityDisplay = cartItem.querySelector(".quantity-display")
            if (quantityDisplay) {
              quantityDisplay.textContent = data.item_quantity
            }

            // Update the item subtotal
            const priceValue = cartItem.querySelector(".price-value")
            if (priceValue) {
              priceValue.textContent = `RWF ${data.item_subtotal.toLocaleString("en-RW")}`
            }
          }

          // Update cart totals
          updateCartTotals(data)

          // Show notification with the message from the server
          showNotification(data.message, "success")
        }
      })
      .catch((error) => {
        console.error("Error updating cart:", error)
        showNotification("Failed to update cart. Please try again.", "error")
      })
  }

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
          updateCartTotals(data)
          // Show notification with the message from the server
          showNotification(data.message, "success")
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

          // Update cart totals
          updateCartTotals(data)

          // Show notification with the message from the server
          showNotification(data.message, "success")

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

  // Function to update cart totals
  function updateCartTotals(data) {
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

    // Update subtotal
    const subtotalElement = document.getElementById("cart-subtotal")
    if (subtotalElement) {
      subtotalElement.textContent = formatCurrency(data.cart_subtotal)
    }

    // Update tax
    const taxElement = document.getElementById("cart-tax")
    if (taxElement) {
      taxElement.textContent = formatCurrency(data.cart_tax)
    }

    // Update shipping
    const shippingElement = document.getElementById("cart-shipping")
    if (shippingElement) {
      shippingElement.textContent = formatCurrency(data.cart_shipping)
    }

    // Update total
    const totalElement = document.getElementById("cart-total")
    if (totalElement) {
      totalElement.textContent = formatCurrency(data.cart_total)
    }
  }

  // Function to show empty cart state
  function showEmptyCart() {
    // Hide the cart items and summary sections
    const cartGrid = document.querySelector(".grid.grid-cols-1.lg\\:grid-cols-3")
    if (cartGrid) {
      cartGrid.classList.add("hidden")
    }

    // Create and show empty cart message
    const container = document.querySelector(".container.mx-auto.px-4")
    if (container) {
      const emptyCartHTML = `
        <div class="bg-white rounded-lg shadow-md p-8 text-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <h2 class="text-2xl font-bold text-gray-800 mb-2">Your cart is empty</h2>
            <p class="text-gray-600 mb-6">Looks like you haven't added any products to your cart yet.</p>
            <a href="/products/" class="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300 inline-flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clip-rule="evenodd" />
                </svg>
                Start Shopping
            </a>
        </div>
      `
      container.insertAdjacentHTML("beforeend", emptyCartHTML)
    }
  }

  // Function to format currency
  function formatCurrency(amount) {
    return "RWF " + Number.parseFloat(amount).toLocaleString("en-RW")
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

            // Show success notification with the message from the server
            showNotification(data.message, "success")

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
      element.textContent = formatCurrency(data.cart_subtotal || data.cart_total)
    })
  }
})

// Modify the showNotification function to properly manage notifications

// Replace the entire showNotification function with this improved version:
function showNotification(message, type = "success") {
  // Clear any existing notifications first
  const existingContainer = document.getElementById("notification-container")
  if (existingContainer) {
    // Fade out all existing notifications
    const existingNotifications = existingContainer.querySelectorAll("div.notification-item")
    existingNotifications.forEach((notification) => {
      notification.classList.add("translate-x-full")
      setTimeout(() => {
        notification.remove()
      }, 300)
    })
  }

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
  notification.className = `notification-item mb-3 p-4 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full ${
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

  // Auto remove after 3 seconds (reduced from 5 seconds)
  setTimeout(() => {
    if (notification.parentNode) {
      notification.classList.add("translate-x-full")
      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove()
        }
      }, 300)
    }
  }, 3000)
}

