// Number of checkboxes and labels
const numberOfCheckboxesdomain = 5;
const labelsdomain = ["Dominio 1", "Dominio 2", "Opção 3", "Opção 4", "Opção 5"];

for (let i = 0; i < numberOfCheckboxesdomain; i++) {
    // Create checkbox element
    const checkbox = document.createElement("input");
    checkbox.setAttribute("type", "checkbox");
    checkbox.setAttribute("id", "domain" + (i + 1));
    checkbox.setAttribute("name", "domain");
    checkbox.setAttribute("value", "Opção " + (i + 1));

    // Create label element
    const label = document.createElement("label");
    label.setAttribute("for", "domain" + (i + 1));
    label.textContent = labelsdomain[i];

    // Append checkbox and label to container
    document.querySelector(".input-group-domain").appendChild(checkbox);
    document.querySelector(".input-group-domain").appendChild(label);
}
