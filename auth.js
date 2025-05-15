// auth.js

async function checkPassword() {
  const input = prompt("Enter access code:");
  const encoder = new TextEncoder();
  const data = encoder.encode(input);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

  const correctHash = "f20b50bc65cf9e1b7cce3c3cf28764905ec870352529e3a70e32cf24f464ed2c";

  if (hashHex !== correctHash) {
    document.body.innerHTML = "<h2 style='color:red; text-align:center;'>Access Denied</h2>";
    throw new Error("Access denied");
  }
}

window.onload = checkPassword;
