function openModal(imageSrc) {
    const modal = document.getElementById("imageModal");
    const modalImage = document.getElementById("modalImage");

    modalImage.src = imageSrc; // Définit la source de l'image dans la modale
    modal.classList.remove("hidden"); // Affiche la modale
}

function closeModal(event) {
    // Ferme la modale si on clique en dehors de l'image ou sur la croix
    if (event.target === document.getElementById("imageModal") || event.target.classList.contains('close')) {
        document.getElementById("imageModal").classList.add("hidden"); // Cache la modale
    }
}
