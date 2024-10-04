// Number of checkboxes and labels
const numberOfCheckboxesSubdomain = 5;
const labelsSubdomain = ["Opção 1", "Opção 2", "Opção 3", "Opção 4", "Opção 5"];

for (let i = 0; i < numberOfCheckboxesSubdomain; i++) {
    // Create checkbox element
    const checkbox = document.createElement("input");
    checkbox.setAttribute("type", "checkbox");
    checkbox.setAttribute("id", "subdomain" + (i + 1));
    checkbox.setAttribute("name", "subdomain");
    checkbox.setAttribute("value", "Opção" + (i + 1));

    // Create label element
    const label = document.createElement("label");
    label.setAttribute("for", "subdomain" + (i + 1));
    label.textContent = labelsSubdomain[i];

    // Append checkbox and label to container
    document.querySelector(".input-group-subdomain").appendChild(checkbox);
    document.querySelector(".input-group-subdomain").appendChild(label);
}
