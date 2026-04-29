// EventHub — Main JavaScript

document.addEventListener('DOMContentLoaded', () => {

  // Auto-select event from URL query param on register page
  const urlParams = new URLSearchParams(window.location.search);
  const preselectedEvent = urlParams.get('event');
  if (preselectedEvent) {
    const select = document.getElementById('event');
    if (select) {
      select.value = preselectedEvent;
    }
  }

  // Animate stat numbers on home page
  animateCounters();

  // Auto-dismiss alerts after 6 seconds
  setTimeout(() => {
    document.querySelectorAll('.alert').forEach(el => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    });
  }, 6000);

  // Copy certificate ID to clipboard
  const certIdEls = document.querySelectorAll('code');
  certIdEls.forEach(el => {
    el.title = 'Click to copy';
    el.style.cursor = 'pointer';
    el.addEventListener('click', () => {
      navigator.clipboard.writeText(el.textContent).then(() => {
        const original = el.textContent;
        el.textContent = '✓ Copied!';
        setTimeout(() => el.textContent = original, 1500);
      });
    });
  });
});

function animateCounters() {
  const counters = document.querySelectorAll('.stat-card .fw-bold');
  counters.forEach(counter => {
    const target = parseInt(counter.textContent, 10);
    if (isNaN(target)) return;
    let current = 0;
    const step = Math.max(1, Math.floor(target / 30));
    const interval = setInterval(() => {
      current = Math.min(current + step, target);
      counter.textContent = current;
      if (current >= target) clearInterval(interval);
    }, 30);
  });
}
