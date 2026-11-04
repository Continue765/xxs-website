const deadline = document.body.dataset.deadline;
if (deadline && document.body.dataset.status === 'open') {
  const closeIfNeeded = () => {
    if (Date.now() < Date.parse(deadline)) return;
    document.querySelectorAll('[data-registration]').forEach(link => {
      const label = document.createElement('span');
      label.className = 'button disabled';
      label.textContent = '报名已截止';
      link.replaceWith(label);
    });
    document.querySelectorAll('[data-registration-qr]').forEach(image => image.remove());
    document.querySelectorAll('[data-status]').forEach(label => label.textContent = '报名已截止');
  };
  closeIfNeeded();
  setInterval(closeIfNeeded, 30000);
}
