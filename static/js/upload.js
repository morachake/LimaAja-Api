class FileUploader {
    constructor(options = {}) {
      this.dropzone = document.getElementById(options.dropzoneId || "documentDropzone")
      this.fileInput = document.getElementById(options.fileInputId || "documentInput")
      this.fileList = document.getElementById(options.fileListId || "uploadedFiles")
      this.maxFileSize = options.maxFileSize || 5 * 1024 * 1024 // 5MB default
      this.allowedTypes = options.allowedTypes || ["image/jpeg", "image/png", "image/gif", "application/pdf"]
  
      this.files = new Set()
      this.init()
    }
  
    init() {
      if (!this.dropzone || !this.fileInput || !this.fileList) return
  
      this.dropzone.addEventListener("click", () => this.fileInput.click())
      this.dropzone.addEventListener("dragover", (e) => this.handleDragOver(e))
      this.dropzone.addEventListener("dragleave", () => this.handleDragLeave())
      this.dropzone.addEventListener("drop", (e) => this.handleDrop(e))
      this.fileInput.addEventListener("change", (e) => this.handleFileSelect(e))
    }
  
    handleDragOver(e) {
      e.preventDefault()
      this.dropzone.classList.add("drag-active")
    }
  
    handleDragLeave() {
      this.dropzone.classList.remove("drag-active")
    }
  
    handleDrop(e) {
      e.preventDefault()
      this.dropzone.classList.remove("drag-active")
      this.processFiles(e.dataTransfer.files)
    }
  
    handleFileSelect(e) {
      this.processFiles(e.target.files)
    }
  
    processFiles(fileList) {
      Array.from(fileList).forEach((file) => {
        if (!this.validateFile(file)) return
  
        if (!this.files.has(file)) {
          this.files.add(file)
          this.addFileToList(file)
        }
      })
    }
  
    validateFile(file) {
      if (file.size > this.maxFileSize) {
        showMessage(`File ${file.name} is too large. Maximum size is ${this.maxFileSize / 1024 / 1024}MB`, "danger")
        return false
      }
  
      if (!this.allowedTypes.includes(file.type)) {
        showMessage(`File ${file.name} is not an allowed type`, "danger")
        return false
      }
  
      return true
    }
  
    addFileToList(file) {
      const fileItem = document.createElement("div")
      fileItem.className = "file-item"
  
      const size = (file.size / 1024 / 1024).toFixed(2)
  
      fileItem.innerHTML = `
              <div class="file-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
                      <polyline points="13 2 13 9 20 9"></polyline>
                  </svg>
              </div>
              <div class="file-info">
                  <div class="file-name">${file.name}</div>
                  <div class="file-size">${size} MB</div>
              </div>
              <div class="file-remove" data-filename="${file.name}">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="18" y1="6" x2="6" y2="18"></line>
                      <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
              </div>
          `
  
      fileItem.querySelector(".file-remove").addEventListener("click", () => this.removeFile(file, fileItem))
      this.fileList.appendChild(fileItem)
    }
  
    removeFile(file, element) {
      this.files.delete(file)
      element.remove()
    }
  
    getFiles() {
      return Array.from(this.files)
    }
  }
  
  // Initialize file uploader if dropzone exists
  document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("documentDropzone")) {
      new FileUploader({
        maxFileSize: 10 * 1024 * 1024, // 10MB
        allowedTypes: ["image/jpeg", "image/png", "image/gif", "application/pdf"],
      })
    }
  })
  
  