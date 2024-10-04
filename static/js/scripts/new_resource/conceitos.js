// Number of checkboxes and labels
const numberOfCheckboxesConcept = 5;
const labelsConcept = ["Opção 1", "Opção 2", "Opção 3", "Opção 4", "Opção 5"];

for (let i = 0; i < numberOfCheckboxesConcept; i++) {
    // Create checkbox element
    const checkbox = document.createElement("input");
    checkbox.setAttribute("type", "checkbox");
    checkbox.setAttribute("id", "concept" + (i + 1));
    checkbox.setAttribute("name", "concept");
    checkbox.setAttribute("value", "Opção " + (i + 1));

    // Create label element
    const label = document.createElement("label");
    label.setAttribute("for", "concept" + (i + 1));
    label.textContent = labelsConcept[i];

    // Append checkbox and label to container
    document.querySelector(".input-group-concept").appendChild(checkbox);
    document.querySelector(".input-group-concept").appendChild(label);
}
