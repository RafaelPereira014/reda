// Number of checkboxes and labels
const numberOfCheckboxesdisciplinas = 5;
const labelsdisciplinas = ["Opção 1", "Opção 2", "Opção 3", "Opção 4", "Opção 5"];

for (let i = 0; i < numberOfCheckboxesdisciplinas; i++) {
    // Create checkbox element
    const checkbox = document.createElement("input");
    checkbox.setAttribute("type", "checkbox");
    checkbox.setAttribute("id", "disci" + (i + 1));
    checkbox.setAttribute("name", "disci");
    checkbox.setAttribute("value", "Opção " + (i + 1));

    // Create label element
    const label = document.createElement("label");
    label.setAttribute("for", "disci" + (i + 1));
    label.textContent = labelsdisciplinas[i];

    // Append checkbox and label to container
    document.querySelector(".input-group-disci").appendChild(checkbox);
    document.querySelector(".input-group-disci").appendChild(label);
}


