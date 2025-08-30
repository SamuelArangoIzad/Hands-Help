document.addEventListener("DOMContentLoaded", () => {
    const menuBtn = document.getElementById("menu-btn");
    const menuLateral = document.getElementById("menu-lateral");

    menuBtn.addEventListener("click", () => {
        menuLateral.classList.toggle("activo");
    });

});
