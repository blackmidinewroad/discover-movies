function toggleDirectors() {
    const list = document.querySelector('.directors-list');
    const button = document.querySelector('.toggle-directors-btn');
    const secondDirector = document.querySelectorAll('.director-link')[1] || document.querySelector('.directed-by');
    const optionalComma = document.querySelector('.optional-comma');

    const isHidden = list.style.display === 'none';

    list.style.display = isHidden ? 'inline' : 'none';
    optionalComma.style.display = isHidden ? 'inline' : 'none';

    button.classList.toggle('show-more', !isHidden);
    button.classList.toggle('show-less', isHidden);
    button.textContent = isHidden ? 'Show Less' : 'Show More';

    if (isHidden) {
        list.insertAdjacentElement('afterend', button);
    } else {
        secondDirector.insertAdjacentElement('afterend', button);
    }
}