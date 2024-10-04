// Get the modal for "Ler mais"
var appModal = document.getElementById("appModal");

// Get the read more buttons
var readmoreButtons = document.getElementsByClassName("readmore");

// Get the close button inside the modal
var appCloseButton = document.querySelector("#appModal .close");

// Iterate over read more buttons and add click event listeners
for (var i = 0; i < readmoreButtons.length; i++) {
    readmoreButtons[i].addEventListener("click", function(event) {
        console.log("Read more button clicked"); // Log click event
        var parentRectangle = event.target.closest(".rectangle");
        var modalTitle = parentRectangle.querySelector("h2").innerText;
        var fullDescription = parentRectangle.querySelector(".full-description").innerText;
        
        console.log("Modal Title: ", modalTitle); // Log modal title
        console.log("Full Description: ", fullDescription); // Log full description
        
        document.getElementById("modalTitle").innerText = modalTitle;
        document.getElementById("modalDescription").innerText = fullDescription;

        // Display the modal
        appModal.style.display = "block";
        document.body.style.overflow = "hidden"; // Prevent background scrolling
    });
}

// When the user clicks on the close button (x), close the modal
appCloseButton.onclick = function() {
    console.log("Close button clicked"); // Log close button click
    appModal.style.display = "none";
    document.body.style.overflow = "auto"; // Allow background scrolling
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
    if (event.target == appModal) {
        console.log("Clicked outside the modal"); // Log outside click
        appModal.style.display = "none";
        document.body.style.overflow = "auto"; // Allow background scrolling
    }
}

// Modal for "Abrir endereço" functionality
var openPathButtons = document.getElementsByClassName("open-path");

for (var i = 0; i < openPathButtons.length; i++) {
    openPathButtons[i].addEventListener("click", function(event) {
        var modalId = event.target.getAttribute("data-modal-id");
        var openPathModal = document.getElementById(modalId);

        console.log("Open path button clicked for modal: ", modalId); // Log modal ID

        openPathModal.style.display = "block";
        document.body.style.overflow = "hidden"; // Prevent background scrolling

        // Close the modal when the close button is clicked
        var closeButton = openPathModal.querySelector(".close");
        closeButton.onclick = function() {
            openPathModal.style.display = "none";
            document.body.style.overflow = "auto"; // Allow background scrolling
        }

        // Close the modal when clicking outside of the modal content
        window.onclick = function(event) {
            if (event.target == openPathModal) {
                openPathModal.style.display = "none";
                document.body.style.overflow = "auto"; // Allow background scrolling
            }
        }
    });
}
