(function () {
  const container = document.querySelector('.availability-check');
  const value = document.getElementById('availability-value');
  const button = document.getElementById('availability-refresh');
  const message = document.getElementById('availability-message');
  if (!container || !value || !button || !message || !container.dataset.availabilityUrl)
    return;

  button.hidden = false;
  button.addEventListener('click', async () => {
    if (button.disabled) return;
    button.disabled = true;
    button.textContent = 'Обновляем…';
    container.setAttribute('aria-busy', 'true');
    message.textContent = 'Проверяем наличие…';

    try {
      const response = await fetch(container.dataset.availabilityUrl, {
        headers: { Accept: 'application/json' },
        cache: 'no-store',
      });
      if (!response.ok) throw new Error('Ошибка запроса');
      const data = await response.json();
      if (
        !data ||
        !Number.isSafeInteger(data.available_count) ||
        data.available_count < 0
      ) {
        throw new Error('Некорректный ответ');
      }
      const available = data.available_count;
      value.textContent = available
        ? `Доступно экземпляров: ${available}`
        : 'Нет доступных экземпляров';
      value.classList.toggle('item-highlight', available > 0);
      message.textContent = 'Данные о наличии обновлены.';
    } catch (error) {
      message.textContent = 'Не удалось обновить наличие. Попробуйте ещё раз.';
    } finally {
      button.disabled = false;
      button.textContent = 'Обновить наличие';
      container.setAttribute('aria-busy', 'false');
    }
  });
})();
