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

  // PWA Push notifications (Web Push)
  async function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
    return outputArray;
  }

  async function getCSRFToken() {
    const el = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return el ? el.value : '';
  }

  async function enablePush() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      alert('Push notifications are not supported in this browser.');
      return;
    }

    const perm = await Notification.requestPermission();
    if (perm !== 'granted') return;

    const pubRes = await fetch('/accounts/push/public-key/');
    const { publicKey } = await pubRes.json();
    if (!publicKey) {
      alert('Push is not configured on server (missing VAPID keys).');
      return;
    }

    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: await urlBase64ToUint8Array(publicKey),
    });

    const csrf = await getCSRFToken();
    await fetch('/accounts/push/subscribe/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
      body: JSON.stringify({ subscription: sub.toJSON() }),
    });

    alert('Notifications enabled!');
  }

  document.querySelectorAll('[data-enable-push="true"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      enablePush();
    });
  });

});
