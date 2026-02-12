
/**
 * Основной JavaScript файл для системы опросов
 */

// Инициализация после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
  // Инициализация форм с кодом опроса
  initPollCodeForms();

  // Инициализация автофокуса
  initAutoFocus();

  // Инициализация подтверждений удаления
  initDeleteConfirmations();
});

/**
 * Инициализация форм ввода кода опроса
 */
function initPollCodeForms() {
  const forms = document.querySelectorAll('#poll-code-form, form[action*="/p/"]');

  forms.forEach(form => {
    if (!form) return;

    form.addEventListener('submit', function(e) {
      e.preventDefault();
      const codeInput = form.querySelector('input[name="code"], input[id="code"]');

      if (!codeInput) return;

      const code = codeInput.value.trim().toUpperCase();

      if (code && /^[A-Za-z0-9]+$/.test(code)) {
        window.location.href = '/p/' + code + '/';
      } else {
        // Показать ошибку
        codeInput.classList.add('ring-2', 'ring-red-500', 'border-red-500');
        const originalPlaceholder = codeInput.placeholder;
        codeInput.placeholder = 'Введите корректный код!';

        setTimeout(() => {
          codeInput.classList.remove('ring-2', 'ring-red-500', 'border-red-500');
          codeInput.placeholder = originalPlaceholder;
        }, 2000);
      }
    });

    // Автоматическое преобразование в верхний регистр
    const codeInput = form.querySelector('input[name="code"], input[id="code"]');
    if (codeInput) {
      codeInput.addEventListener('input', function(e) {
        e.target.value = e.target.value.toUpperCase();
      });
    }
  });
}

/**
 * Инициализация автофокуса для полей ввода
 */
function initAutoFocus() {
  const autofocusInputs = document.querySelectorAll('input[autofocus], textarea[autofocus]');
  autofocusInputs.forEach(input => {
    if (input && !input.disabled) {
      setTimeout(() => input.focus(), 100);
    }
  });
}


  function onReady(cb) {
    if (document.readyState === "complete" || document.readyState === "interactive") {
      cb();
    } else {
      document.addEventListener("DOMContentLoaded", cb, { once: true });
    }
  }

  onReady(function () {
    // 1. Auto-focus poll code input (with nice scroll into view)
    var codeInput = document.getElementById("code");
    if (codeInput) {
      codeInput.focus({ preventScroll: true });
      codeInput.scrollIntoView({ behavior: "smooth", block: "center" });
      codeInput.classList.add("poll-code-input");
    }

    // 2. Auto-hide flash messages after a delay
    var alertsContainers = document.querySelectorAll("[role='alert']");
    if (alertsContainers.length) {
      setTimeout(function () {
        alertsContainers.forEach(function (container) {
          container.style.transition = "opacity 250ms ease, transform 250ms ease";
          container.style.opacity = "0";
          container.style.transform = "translateY(-4px)";
          setTimeout(function () {
            if (container && container.parentElement) {
              container.parentElement.removeChild(container);
            }
          }, 260);
        });
      }, 4200);
    }

    // 3. Helper: click-to-select for any readonly code blocks (e.g., access codes)
    document.querySelectorAll("code").forEach(function (codeEl) {
      if (codeEl.closest("[data-click-select]")) {
        codeEl.style.cursor = "pointer";
        codeEl.addEventListener("click", function () {
          var range = document.createRange();
          range.selectNodeContents(codeEl);
          var sel = window.getSelection();
          sel.removeAllRanges();
          sel.addRange(range);
        });
      }
    });
  });



// Экспорт для использования в других скриптах
window.PollSystem = {
  showNotification,
  copyToClipboard,
};

