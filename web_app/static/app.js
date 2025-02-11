document.addEventListener("DOMContentLoaded", function () {
    console.log("Dashboard loaded successfully!");

    const uploadForm = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const fileEntries = document.getElementById("fileEntries");
    const tableContainer = document.getElementById("tableContainer");
    const responseMessage = document.getElementById("responseMessage");

    // Handle File Upload
    if (uploadForm) {
        uploadForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const formData = new FormData(uploadForm);

            try {
                const response = await fetch("/upload", {
                    method: "POST",
                    body: formData,
                });

                const result = await response.json();

                if (result.error) {
                    responseMessage.textContent = result.error;
                    responseMessage.style.display = "block";
                    responseMessage.className = "text-danger";
                } else {
                    // Update response message
                    responseMessage.textContent = `Dataset "${result.filename}" loaded successfully!`;
                    responseMessage.style.display = "block";
                    responseMessage.className = "text-success";

                    // Add new entry to file entries list
                    const entryItem = document.createElement("li");
                    entryItem.className = "list-group-item d-flex justify-content-between align-items-center";
                    entryItem.innerHTML = `
                        <span>${result.filename}</span>
                        <div>
                            <button class="btn btn-sm btn-primary me-1" onclick="viewTable('${encodeURIComponent(result.table)}')">View Table</button>
                            <button class="btn btn-sm btn-danger me-1" onclick="deleteEntry(this)">Delete</button>
                            <button class="btn btn-sm btn-secondary" onclick="refreshEntry()">Refresh</button>
                        </div>
                    `;
                    fileEntries.appendChild(entryItem);

                    // Render the table
                    tableContainer.innerHTML = decodeURIComponent(result.table);
                }
            } catch (error) {
                responseMessage.textContent = "An error occurred while uploading the file.";
                responseMessage.style.display = "block";
                responseMessage.className = "text-danger";
                console.error(error);
            }
        });
    }
});

// View Table Function
function viewTable(tableHtml) {
    const tableContainer = document.getElementById("tableContainer");
    //tableContainer.innerHTML = decodeURIComponent(tableHtml);
    tableContainer.innerHTML = decodeURIComponent(result.table);
}

// Delete Entry Function
function deleteEntry(button) {
    const listItem = button.closest("li");
    listItem.remove();

    const tableContainer = document.getElementById("tableContainer");
    tableContainer.innerHTML = `<p class="text-muted">No dataset is currently rendered. Upload and select a file to view the table.</p>`;
}

// Refresh Entry Function (Placeholder for now)
function refreshEntry() {
    alert("Refresh functionality is not implemented yet.");
}

// Sidebar Toggle
document.getElementById("toggle-sidebar").addEventListener("click", function() {
    let sidebar = document.getElementById("sidebar");
    if (sidebar.style.width === "200px") {
        sidebar.style.width = "60px";
    } else {
        sidebar.style.width = "200px";
    }
});

// Content Viewer Toggle
function openContentViewer() {
    document.getElementById("content-viewer").classList.add("open");
}
function closeContentViewer() {
    document.getElementById("content-viewer").classList.remove("open");
}

// Highlight Active Navigation Item
const currentPage = window.location.pathname;
document.querySelectorAll("#sidebar ul li a").forEach(link => {
    if (link.getAttribute("href") === currentPage) {
        link.classList.add("active");
    }
});

// App Settings Modal
function openSettings() {
    document.getElementById("settings-modal").style.display = "block";
}
function closeSettings() {
    document.getElementById("settings-modal").style.display = "none";
}

// Theme Toggle (Dark Mode)
function toggleTheme() {
    document.body.classList.toggle("dark-mode");
    document.querySelector(".navbar").classList.toggle("dark-mode");

    localStorage.setItem("darkMode", document.body.classList.contains("dark-mode"));
}

// Restore Theme Preference
if (localStorage.getItem("darkMode") === "true") {
    document.body.classList.add("dark-mode");
    document.querySelector(".navbar").classList.add("dark-mode");
}

