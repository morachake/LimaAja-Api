// Placeholder image fix
document.addEventListener("DOMContentLoaded", () => {
    // Function to handle image loading errors
    function handleImageError(img, fallbackText) {
      // If the image already has an onerror handler, don't add another one
      if (img.getAttribute("data-error-handled")) return
  
      // Mark this image as handled
      img.setAttribute("data-error-handled", "true")
  
      // Set a local fallback image based on the text
      let fallbackImage = "/static/images/placeholder.jpg"
  
      if (fallbackText) {
        const lowerText = fallbackText.toLowerCase()
        if (lowerText.includes("fresh") || lowerText.includes("produce")) {
          fallbackImage = "/static/images/placeholder-produce.jpg"
        } else if (lowerText.includes("maize")) {
          fallbackImage = "/static/images/placeholder-maize.jpg"
        } else if (lowerText.includes("dania")) {
          fallbackImage = "/static/images/placeholder-dania.jpg"
        }
      }
  
      img.src = fallbackImage
  
      // Prevent further error handling to avoid loops
      img.onerror = null
    }
  
    // Find all images with placeholder.com in their src
    const placeholderImages = document.querySelectorAll('img[src*="placeholder.com"]')
    placeholderImages.forEach((img) => {
      // Extract the text from the URL if possible
      let fallbackText = ""
      const match = img.src.match(/text=([^&]+)/)
      if (match && match[1]) {
        fallbackText = decodeURIComponent(match[1])
      }
  
      // Set up error handling
      img.onerror = function () {
        handleImageError(this, fallbackText)
      }
  
      // Force reload to trigger error handler if needed
      if (img.complete && img.naturalHeight === 0) {
        handleImageError(img, fallbackText)
      }
    })
  
    // Also handle images with onerror attributes that might be failing
    const errorHandledImages = document.querySelectorAll("img[onerror]")
    errorHandledImages.forEach((img) => {
      if (img.complete && img.naturalHeight === 0) {
        // Extract text from alt attribute or use empty string
        const fallbackText = img.alt || ""
        handleImageError(img, fallbackText)
      }
    })
  })
  
  