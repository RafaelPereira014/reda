// Handle "Abrir endereço" buttons
var openPathButtons = document.getElementsByClassName("open-path");

for (var i = 0; i < openPathButtons.length; i++) {
    openPathButtons[i].addEventListener("click", function(event) {
        var modalId = event.target.getAttribute("data-modal-id");
        var modal = document.getElementById(modalId);
        modal.style.display = "block";
    });
}

// Handle "Ler mais" buttons
var readmoreButtons = document.getElementsByClassName("readmore");

for (var i = 0; i < readmoreButtons.length; i++) {
    readmoreButtons[i].addEventListener("click", function(event) {
        var parentRectangle = event.target.closest(".rectangle");
        var modalTitle = parentRectangle.querySelector("h2").innerText;
        var fullDescription = parentRectangle.querySelector(".full-description").innerText;
        
        // Find or create a modal for "Ler mais"
        var modalId = "readmoreModal-" + i;
        var modal = document.getElementById(modalId);
        
        if (!modal) {
            modal = document.createElement("div");
            modal.id = modalId;
            modal.className = "modal";
            modal.innerHTML = `
                <div class="modal-content">
                    <h2 id="modalTitle">${modalTitle}</h2>
                    <p id="modalDescription">${fullDescription}</p>
                    <div class="button-container">
                        <button class="close-modal">Fechar</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            
            // Add event listener to the close button
            modal.querySelector(".close-modal").addEventListener("click", function() {
                modal.style.display = "none";
            });
        }

        modal.style.display = "block";
    });
}

// Handle "Não, obrigado" buttons
var closeButtons = document.getElementsByClassName("close-modal");

for (var i = 0; i < closeButtons.length; i++) {
    closeButtons[i].addEventListener("click", function(event) {
        var modal = event.target.closest(".modal");
        modal.style.display = "none";
    });
}

// Handle modal close actions when clicking outside the modal
window.onclick = function(event) {
    var modals = document.getElementsByClassName("modal");
    for (var i = 0; i < modals.length; i++) {
        if (event.target == modals[i]) {
            modals[i].style.display = "none";
        }
    }
};
