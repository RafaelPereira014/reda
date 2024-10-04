// Number of checkboxes
const numberOfCheckboxes = 6;
                
// Labels for the checkboxes
const labels = ["7º", "8º", "9º", "10º", "11º", "12º"];

for (let i = 0; i < numberOfCheckboxes; i++) {
    // Create checkbox element
    const checkbox = document.createElement("input");
    checkbox.setAttribute("type", "checkbox");
    checkbox.setAttribute("id", "escolaridade" + (i + 1));
    checkbox.setAttribute("name", "escolaridade");
    checkbox.setAttribute("value", "Opção " + (i + 1));

    // Create label element
    const label = document.createElement("label");
    label.setAttribute("for", "escolaridade" + (i + 1));
    label.textContent = labels[i];

    // Append checkbox and label to container
    document.querySelector(".input-group-escolaridade").appendChild(checkbox);
    document.querySelector(".input-group-escolaridade").appendChild(label);
}