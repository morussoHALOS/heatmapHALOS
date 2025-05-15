// auth.js

async function checkPassword() {
  const input = prompt("Enter access code:");
  const encoder = new TextEncoder();
  const data = encoder.encode(input);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

  const correctHash = "0d84b5eaa3e0a7caaef9e68c5291d9b9c39a81fbe56f2ad0e2d2d430be037ffe";

  if (hashHex !== correctHash) {
    document.body.innerHTML = "<h2 style='color:red; text-align:center;'>Access Denied</h2>";
    throw new Error("Access denied");
  }
}

window.onload = checkPassword;
