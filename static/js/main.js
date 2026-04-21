// Tumakuru Civic Portal — Main JS

document.addEventListener('DOMContentLoaded', () => {

  // Auto-dismiss alerts after 6 seconds
  document.querySelectorAll('.msg-alert').forEach(el => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    }, 6000);
  });

  // Animate progress bars
  document.querySelectorAll('.progress-bar[data-target]').forEach(bar => {
    const target = parseFloat(bar.getAttribute('data-target'));
    bar.style.width = '0%';
    setTimeout(() => { bar.style.width = target + '%'; }, 300);
  });

  // Animate stat numbers
  document.querySelectorAll('.stat-number').forEach(el => {
    const target = parseInt(el.textContent, 10);
    if (isNaN(target) || target === 0) return;
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 40));
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current;
      if (current >= target) clearInterval(timer);
    }, 30);
  });

  // Scroll reveal for fade-in-up elements
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.fade-in-up').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(el);
  });

  // Active nav link highlighting
  const path = window.location.pathname;
  document.querySelectorAll('.main-nav .nav-link').forEach(link => {
    if (link.getAttribute('href') === path) {
      link.classList.add('text-saffron');
      link.style.color = 'var(--saffron)';
    }
  });

});
