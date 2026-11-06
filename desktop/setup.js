document.getElementById('form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = document.getElementById('connect');
  button.disabled = true;
  document.getElementById('error').textContent = '';
  try {
    await window.horizonteSetup.connect(document.getElementById('server').value);
  } catch (error) {
    document.getElementById('error').textContent = error.message;
    button.disabled = false;
  }
});
