// index.js



function f() {
    document.getElementsByClassName('dropdown')[0].classList.toggle('down');
    document.getElementsByClassName('arrow')[0].classList.toggle('gone');
    if (document.getElementsByClassName('dropdown')[0].classList.contains('down')) {
      setTimeout(function() {
        document.getElementsByClassName('dropdown')[0].style.overflow = 'visible'
      }, 500)
    } else {
      document.getElementsByClassName('dropdown')[0].style.overflow = 'hidden'
    }
  }

  function searchResources() {
    const searchInput = document.getElementById("searchInput").value.toLowerCase();
    const resources = document.querySelectorAll("#my-resources .rectangle");
    
    resources.forEach(resource => {
        const resourceName = resource.querySelector("img").alt.toLowerCase();
        if (resourceName.includes(searchInput)) {
            resource.style.display = "block";
        } else {
            resource.style.display = "none";
        }
    });
}
// Define an array to hold all resources
const allResources = document.querySelectorAll("#my-resources .rectangle");
// Set the number of resources per page
const resourcesPerPage = 4;
// Initialize the current page index
let currentPage = 0;

// Function to display resources based on current page
function displayResources() {
    const startIndex = currentPage * resourcesPerPage;
    const endIndex = startIndex + resourcesPerPage;
    // Hide all resources
    allResources.forEach(resource => {
        resource.style.display = "none";
    });
    // Display resources for the current page
    for (let i = startIndex; i < endIndex && i < allResources.length; i++) {
        allResources[i].style.display = "block";
    }
}

// Initial display of resources
displayResources();

// Function to navigate to the previous page
function previousPage() {
    if (currentPage > 0) {
        currentPage--;
        displayResources();
    }
}

// Function to navigate to the next page
function nextPage() {
    if (currentPage < Math.ceil(allResources.length / resourcesPerPage) - 1) {
        currentPage++;
        displayResources();
    }
}

// Function to handle search
function searchResources() {
    const searchInput = document.getElementById("searchInput").value.toLowerCase();
    // Filter resources based on search query
    const filteredResources = Array.from(allResources).filter(resource => {
        const resourceName = resource.querySelector("img").alt.toLowerCase();
        return resourceName.includes(searchInput);
    });
    // Update the displayed resources with filtered results
    currentPage = 0;
    allResources.forEach(resource => {
        if (filteredResources.includes(resource)) {
            resource.style.display = "block";
        } else {
            resource.style.display = "none";
        }
    });
}







