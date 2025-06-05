document.addEventListener('DOMContentLoaded', () => {
    const buyTab = document.querySelector('header h1:nth-child(1)');
    const sellTab = document.querySelector('header h1:nth-child(2)');

    buyTab.addEventListener('click', () => {
        buyTab.classList.remove('inactive');
        sellTab.classList.add('inactive');
        // Здесь можно добавить логику для обновления списка предложений
    });

    sellTab.addEventListener('click', () => {
        sellTab.classList.remove('inactive');
        buyTab.classList.add('inactive');
        // Здесь можно добавить логику для обновления списка предложений
    });
});
