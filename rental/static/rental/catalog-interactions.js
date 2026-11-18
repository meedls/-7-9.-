(function () {
  const cards = Array.from(document.querySelectorAll('.card[data-game-id]'));
  const search = document.getElementById('catalog-search');
  const filterHint = document.getElementById('catalog-filter-hint');
  const filterStatus = document.getElementById('catalog-filter-status');

  // Фильтр не меняет серверный поиск: кнопка формы по-прежнему ищет во всей базе.
  if (search && filterHint && filterStatus && cards.length) {
    filterHint.hidden = false;
    function filterPage() {
      const query = search.value.trim().toLocaleLowerCase('ru-RU');
      let visible = 0;
      cards.forEach((card) => {
        const title = card.querySelector('h2').textContent.toLocaleLowerCase('ru-RU');
        const matches = title.includes(query);
        card.hidden = !matches;
        if (matches) visible += 1;
      });
      filterStatus.hidden = !query;
      filterStatus.textContent = query
        ? `На этой странице найдено игр: ${visible}. Для поиска по всему каталогу нажмите «Найти игру».`
        : '';
    }
    search.addEventListener('input', filterPage);
    filterPage();
  }

  const buttons = Array.from(document.querySelectorAll('.favorite-button'));
  const favoritesNote = document.getElementById('favorites-note');
  const favoritesStatus = document.getElementById('favorites-status');
  if (!buttons.length || !favoritesNote || !favoritesStatus) return;

  const storageKey = 'game-rental-favorites-v1';

  function announce(message) {
    favoritesStatus.textContent = message;
    favoritesStatus.hidden = false;
  }

  function readFavorites() {
    const raw = window.localStorage.getItem(storageKey);
    if (raw === null) return new Set();
    const saved = JSON.parse(raw);
    if (
      !Array.isArray(saved) ||
      saved.some((id) => typeof id !== 'string' || !/^\d+$/.test(id))
    ) {
      throw new Error('Некорректный формат избранного');
    }
    return new Set(saved);
  }

  function updateButtons(favorites) {
    buttons.forEach((button) => {
      const selected = favorites.has(button.dataset.favoriteId);
      button.setAttribute('aria-pressed', String(selected));
      button.setAttribute(
        'aria-label',
        selected
          ? `Удалить ${button.dataset.title} из избранного`
          : `Добавить ${button.dataset.title} в избранное`,
      );
      button.textContent = selected ? 'В избранном' : 'В избранное';
    });
  }

  function storageUnavailable() {
    buttons.forEach((button) => {
      button.disabled = true;
    });
    announce('Избранное недоступно: проверьте доступ браузера к локальному хранилищу.');
  }

  buttons.forEach((button) => {
    button.hidden = false;
  });
  favoritesNote.hidden = false;
  let favorites;
  try {
    favorites = readFavorites();
    updateButtons(favorites);
  } catch (error) {
    storageUnavailable();
    return;
  }

  buttons.forEach((button) => {
    button.addEventListener('click', () => {
      const id = button.dataset.favoriteId;
      const next = new Set(favorites);
      const selected = next.has(id);
      if (selected) next.delete(id);
      else next.add(id);
      try {
        window.localStorage.setItem(storageKey, JSON.stringify(Array.from(next)));
        favorites = next;
        updateButtons(favorites);
        announce(
          selected ? 'Игра удалена из избранного.' : 'Игра добавлена в избранное.',
        );
      } catch (error) {
        storageUnavailable();
      }
    });
  });

  window.addEventListener('storage', (event) => {
    if (event.key !== storageKey && event.key !== null) return;
    try {
      favorites = readFavorites();
      updateButtons(favorites);
    } catch (error) {
      storageUnavailable();
    }
  });
})();
