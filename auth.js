// auth.js

async function checkPassword() {
  const input = prompt("Enter access code:");
  const encoder = new TextEncoder();
  const data = encoder.encode(input);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

  // ✅ Correct SHA-256 hash for "halos2024"
  const correctHash = "f68e511cfddbf9c7aef8f46277de3a4dcf6df73d6a8df1191849f1f11f3d3617";

  if (hashHex !== correctHash) {
    document.body.innerHTML = "<h2 style='color:red; text-align:center;'>Access Denied</h2>";
    throw new Error("Access denied");
  }
}

window.onload = checkPassword;
