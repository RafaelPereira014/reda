document.addEventListener("DOMContentLoaded", function() {
    let slideIndex = 0;
    const slides = document.querySelectorAll(".carousel-item");
    const totalSlides = slides.length;

    function showSlide(index) {
        const carouselInner = document.querySelector(".carousel-inner");
        carouselInner.style.transform = `translateX(-${index * 100}%)`;
    }

    function moveSlide(n) {
        slideIndex += n;
        if (slideIndex >= totalSlides) {
            slideIndex = 0;
        }
        if (slideIndex < 0) {
            slideIndex = totalSlides - 1;
        }
        showSlide(slideIndex);
    }

    // Auto slide
    setInterval(() => {
        moveSlide(1);
    }, 10000); // Change slide every 10 seconds

    document.querySelector(".prev").addEventListener("click", () => moveSlide(-1));
    document.querySelector(".next").addEventListener("click", () => moveSlide(1));
});
