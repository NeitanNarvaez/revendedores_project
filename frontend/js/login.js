document.querySelector('#login-form').addEventListener('submit', async event => {
  event.preventDefault();
  const button = event.target.querySelector('button');
  const message = document.querySelector('#message');
  button.disabled = true; message.hidden = true;
  try {
    const result = await api('/auth/login', 'POST', {correo: document.querySelector('#correo').value.trim(), contrasena: document.querySelector('#contrasena').value});
    session.save(result.access_token); location.href = 'index.html';
  } catch (error) {
    message.className = 'alert alert-danger'; message.textContent = error.message; message.hidden = false;
  } finally { button.disabled = false; }
});
