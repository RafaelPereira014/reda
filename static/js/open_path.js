// Get the modal
var openPathModal = document.getElementById("openPathModal");

// Get the button that opens the modal
var openPathButtons = document.getElementsByClassName("open-path");

// Get the "Compreendi" and "Não, obrigado" buttons inside the modal
var compreendiButton = document.querySelector("#openPathModal .compreendi");
var closeButton = document.querySelector("#openPathModal .close-modal");

// Iterate over "Abrir endereço" buttons and add click event listeners
for (var i = 0; i < openPathButtons.length; i++) {
    openPathButtons[i].addEventListener("click", function(event) {
        // Display the modal
        openPathModal.style.display = "block";
    });
}

// Close the modal when clicking "Não, obrigado"
closeButton.onclick = function() {
    openPathModal.style.display = "none";
}

// Close the modal when clicking outside the modal content
window.onclick = function(event) {
    if (event.target == openPathModal) {
        openPathModal.style.display = "none";
    }
}

// Handle "Compreendi" button click (for redirection, replace "#" with your desired URL)
compreendiButton.onclick = function() {
    window.location.href = "#"; // Replace "#" with your desired URL
}
