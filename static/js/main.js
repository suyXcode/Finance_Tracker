/**
 * static/js/main.js
 * Personal Finance Tracker — Frontend JS
 */

'use strict';

// ── Sidebar toggle ────────────────────────────────────────
(function initSidebar() {
  const hamburger = document.getElementById('hamburger');
  const sidebar   = document.getElementById('sidebar');
  const overlay   = document.getElementById('sidebar-overlay');

  if (!hamburger || !sidebar) return;

  hamburger.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    if (overlay) overlay.classList.toggle('d-none');
  });

  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.add('d-none');
    });
  }
})();


// ── Auto-dismiss flash messages ───────────────────────────
(function autoDismissAlerts() {
  const alerts = document.querySelectorAll('.alert-autodismiss');
  alerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 4500);
  });
})();


// ── Confirm delete modal ──────────────────────────────────
(function confirmDelete() {
  // Any button with data-confirm="..." shows a native confirm dialog
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', e => {
      const msg = btn.dataset.confirm || 'Are you sure?';
      if (!window.confirm(msg)) e.preventDefault();
    });
  });
})();


// ── Active sidebar link ───────────────────────────────────
(function markActiveLink() {
  const path  = window.location.pathname;
  const links = document.querySelectorAll('.sidebar-nav .nav-link');
  links.forEach(link => {
    if (link.getAttribute('href') && path.startsWith(link.getAttribute('href'))) {
      link.classList.add('active');
    }
  });
})();


// ── Budget progress bar animation ────────────────────────
(function animateBudgetBars() {
  const bars = document.querySelectorAll('.budget-bar-fill[data-width]');
  // Use requestAnimationFrame so CSS transition plays after paint
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      bars.forEach(bar => {
        bar.style.width = bar.dataset.width + '%';
      });
    });
  });
})();


// ── Date range picker sync ────────────────────────────────
(function syncDateRange() {
  const fromInput = document.getElementById('id_date_from');
  const toInput   = document.getElementById('id_date_to');
  if (!fromInput || !toInput) return;

  fromInput.addEventListener('change', () => {
    if (toInput.value && fromInput.value > toInput.value) {
      toInput.value = fromInput.value;
    }
    toInput.min = fromInput.value;
  });
})();


// ── Transaction type toggle (color hint) ──────────────────
(function transactionTypeHint() {
  const typeSelect = document.getElementById('id_type');
  const amountInput = document.getElementById('id_amount');
  if (!typeSelect || !amountInput) return;

  const update = () => {
    amountInput.style.borderColor =
      typeSelect.value === 'income' ? '#2dc653' :
      typeSelect.value === 'expense' ? '#e63946' : '';
  };
  typeSelect.addEventListener('change', update);
  update();
})();
