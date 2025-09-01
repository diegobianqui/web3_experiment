# Django MetaMask Login

Passwordless authentication using an Ethereum wallet (MetaMask) with a Django backend. The flow issues a server-generated nonce, asks the wallet to sign a SIWE-style message, verifies the signature on the backend, and establishes a Django session.

## Features
- SIWE-style challenge/response (nonce + signed message)
- Server-side signature verification (web3/eth-account)
- Session-based login/logout compatible with Django auth
- Minimal front-end example with MetaMask (ethers.js)

## Prerequisites
- Python 3.10+ and pip
- Node.js (optional, for front-end demo)
- MetaMask installed in the browser
- An Ethereum chain ID your app targets (e.g., 1 Mainnet, 11155111 Sepolia)

## Quick start
1) Create and activate a virtualenv, then install Python dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2) Configure environment:
- Create a `.env` file (or use your preferred config system) and set at minimum:
```bash
DJANGO_SECRET_KEY=replace-me
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1
SITE_DOMAIN=http://127.0.0.1:8000
ETHEREUM_CHAIN_ID=11155111
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
```

3) Run database migrations:
```bash
python manage.py migrate
```

4) Start the server:
```bash
python manage.py runserver
```

5) Open your client app (or use the sample snippet below) and connect MetaMask.

## How it works (SIWE-style)
- Client requests a nonce from the backend.
- Server returns a unique nonce tied to the session.
- Client builds a message including: domain, address, URI, version, chainId, nonce, issuedAt (and optionally expiration).
- MetaMask signs this message with the user’s private key.
- Client sends address + signature (and message details) to backend.
- Backend verifies signature → logs user in (session cookie).
- Client can call authenticated endpoints; logout clears the session.

## API (typical shape)
Adjust paths/names to match your code if they differ.

- GET /auth/nonce/
  - Response: `{ "nonce": "abcd1234" }`
  - Notes: Usually sets/associates nonce with the session.

- POST /auth/verify/
  - Request JSON (example):
    ```json
    {
      "address": "0xUserAddress",
      "signature": "0xSignedMessage",
      "message": "Full SIWE-style message with the returned nonce",
      "chainId": 11155111
    }
    ```
  - Response: `{ "ok": true, "address": "0xUserAddress" }`
  - Effect: Creates/links a Django user to the address and logs them in.

- GET /auth/me/
  - Response: `{ "authenticated": true, "address": "0xUserAddress" }`
  - Requires session.

- POST /auth/logout/
  - Response: `{ "ok": true }`
  - Clears session.

CSRF: For POST requests from a browser, include the CSRF token header. Example with fetch:
```js
fetch("/auth/verify/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": getCookie("csrftoken")
  },
  credentials: "include",
  body: JSON.stringify(/* ... */)
});
```

## Minimal front-end example (MetaMask + ethers.js)
This snippet illustrates the flow. Replace endpoint URLs to match your app.

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/6.11.1/ethers.umd.min.js" integrity="sha512-C8tWvQO8Wk3GZpD4+0sppb3yGvAnO7x1bTBDRdJkR1kNUd0Y87R33oS0ptkODdJBbBMpC7Nzo0h3XvNU1pS7xA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
<script>
async function loginWithMetaMask() {
  if (!window.ethereum) {
    alert("MetaMask not detected");
    return;
  }

  const resp = await fetch("/auth/nonce/", { credentials: "include" });
  const { nonce } = await resp.json();

  const provider = new ethers.BrowserProvider(window.ethereum);
  await provider.send("eth_requestAccounts", []);
  const signer = await provider.getSigner();
  const address = await signer.getAddress();

  // Build a SIWE-style message (simplified)
  const domain = window.location.host;
  const uri = window.location.origin;
  const chainId = 11155111; // keep in sync with backend
  const statement = "Sign in with Ethereum to the app.";

  const message = [
    `${domain} wants you to sign in with your Ethereum account:`,
    address,
    "",
    statement,
    "",
    `URI: ${uri}`,
    `Version: 1`,
    `Chain ID: ${chainId}`,
    `Nonce: ${nonce}`,
    `Issued At: ${new Date().toISOString()}`
  ].join("\n");

  const signature = await signer.signMessage(message);

  // Send to backend
  const verify = await fetch("/auth/verify/", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken") // if Django CSRF is enabled
    },
    body: JSON.stringify({ address, signature, message, chainId })
  });

  const data = await verify.json();
  if (data.ok) {
    console.log("Logged in as:", data.address);
  } else {
    console.error("Login failed:", data);
  }
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}
</script>
<button onclick="loginWithMetaMask()">Login with MetaMask</button>
```

## Development tips
- Use credentials: "include" in fetch so cookies (session/CSRF) are sent.
- Ensure ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS include your dev host/port.
- If you proxy from a frontend dev server, forward cookies and headers.

## Security considerations
- Always bind signature verification to a server-issued nonce stored in the session; one-time use.
- Include domain, uri, chainId, issuedAt (and optional expiration) in the message.
- Validate chainId to avoid signature replay across networks.
- Enforce HTTPS in production; set Secure/HttpOnly/SameSite cookies appropriately.
- Never accept signatures over arbitrary messages; only your canonical SIWE message.
- Rate-limit nonce issuance and verify attempts.

## Troubleshooting
- Invalid signature: confirm the exact message bytes on client match what backend verifies.
- Wrong chain: ensure the wallet network chainId matches ETHEREUM_CHAIN_ID.
- CSRF failures: send X-CSRFToken and cookies; add your origin to CSRF_TRUSTED_ORIGINS.
- Time drift: if you validate issuedAt/expiration, allow a small clock skew or use server time.
- Session not sticking: include credentials: "include" and serve over consistent domain/port.

## Production deployment
- Set DEBUG=0, configure ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, and secure cookies.
- Use a persistent database; run migrations on deploy.
- Put Django behind a reverse proxy (nginx) with HTTPS.
- Consider rotating nonces and cleaning stale sessions regularly.

## License
MIT

