document.addEventListener("DOMContentLoaded", () => {
    const dropdowns = document.querySelectorAll(".dropdown");

    dropdowns.forEach(dropdown => {
        const menu = dropdown.querySelector(".dropdown-menu");
        let openTimeout;
        let closeTimeout;

        dropdown.addEventListener("mouseenter", () => {
            clearTimeout(closeTimeout);
            openTimeout = setTimeout(() => {
                dropdown.classList.add("show");
                menu.classList.add("show");
            }, 150);
        });

        dropdown.addEventListener("mouseleave", () => {
            clearTimeout(openTimeout);
            closeTimeout = setTimeout(() => {
                dropdown.classList.remove("show");
                menu.classList.remove("show");
            }, 200);
        });
    });
});