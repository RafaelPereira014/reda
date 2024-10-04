// Get the element containing the date
const createdAtElement = document.getElementById('created_at');

// Extract the date string
const dateString = createdAtElement.textContent.trim();

// Convert the date string to a JavaScript Date object
const date = new Date(dateString);

// Array of month names in Portuguese
const months = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", 
                "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];

// Format the date in the desired format
const formattedDate = `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;

// Update the content of the element with the formatted date
createdAtElement.textContent = formattedDate;
