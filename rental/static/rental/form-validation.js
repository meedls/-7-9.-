(function () {
  document.querySelectorAll('form[data-client-validation]').forEach((form) => {
    const fields = Array.from(
      form.querySelectorAll('input:not([type="hidden"]), textarea, select'),
    );
    const initialInvalid = new WeakMap(
      fields.map((field) => [field, field.getAttribute('aria-invalid')]),
    );

    function clearError(field) {
      const errorId = `${field.id}-client-error`;
      const error = document.getElementById(errorId);
      if (error) error.remove();

      const describedBy = (field.getAttribute('aria-describedby') || '')
        .split(/\s+/)
        .filter((id) => id && id !== errorId);
      if (describedBy.length)
        field.setAttribute('aria-describedby', describedBy.join(' '));
      else field.removeAttribute('aria-describedby');

      const original = initialInvalid.get(field);
      if (original === null) field.removeAttribute('aria-invalid');
      else field.setAttribute('aria-invalid', original);
    }

    function showError(field, message) {
      const error = document.createElement('div');
      error.id = `${field.id}-client-error`;
      error.className = 'client-field-error';
      error.setAttribute('role', 'alert');
      error.textContent = message;
      field.closest('.account-field').appendChild(error);

      const describedBy = (field.getAttribute('aria-describedby') || '')
        .split(/\s+/)
        .filter(Boolean);
      describedBy.push(error.id);
      field.setAttribute('aria-describedby', describedBy.join(' '));
      field.setAttribute('aria-invalid', 'true');
    }

    function errorMessage(field) {
      if (field.disabled) return '';
      const value = field.type === 'password' ? field.value : field.value.trim();
      if (field.required && !value) return 'Заполните это поле.';
      if (!value) return '';
      if (field.type === 'email' && field.validity.typeMismatch)
        return 'Введите корректный адрес электронной почты.';
      if (field.type === 'tel') {
        const digits = value.replace(/\D/g, '');
        if (
          !/^\+?[\d\s().-]+$/.test(value) ||
          digits.length < 7 ||
          digits.length > 15
        ) {
          return 'Введите номер телефона: от 7 до 15 цифр.';
        }
      }
      if (field.minLength > 0 && value.length < field.minLength) {
        return `Введите не менее ${field.minLength} символов.`;
      }
      if (field.maxLength > 0 && value.length > field.maxLength) {
        return `Введите не более ${field.maxLength} символов.`;
      }
      if (field.name === 'password1' && value.length < 8)
        return 'Пароль должен содержать не менее 8 символов.';
      if (field.name === 'password2' && field.value !== form.elements.password1.value)
        return 'Пароли не совпадают.';
      return '';
    }

    fields.forEach((field) => {
      field.addEventListener('input', () => {
        clearError(field);
        if (field.name === 'password1' && form.elements.password2)
          clearError(form.elements.password2);
      });
    });

    form.addEventListener('submit', (event) => {
      let firstInvalid = null;
      fields.forEach((field) => {
        clearError(field);
        const message = errorMessage(field);
        if (message) {
          showError(field, message);
          if (!firstInvalid) firstInvalid = field;
        }
      });
      if (firstInvalid) {
        event.preventDefault();
        firstInvalid.focus();
      }
    });
  });
})();
