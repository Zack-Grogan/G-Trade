# Authentication

The Gateway API authenticates requests with **JSON Web Tokens (JWT)**. After login, you send the session token on **all** subsequent REST calls (and for SignalR; see [Realtime overview](../realtime/overview.md)) until the token expires.

**Token lifetime:** session tokens are valid for **24 hours**. Use [Validate session](#validate-session) to refresh when needed.

**Typical header for authenticated REST calls:**

```http
Authorization: Bearer <token>
Content-Type: application/json
```

Exact header requirements follow your client library; the important part is supplying the JWT the API issued at login.

---

## Authenticate (API key)

Use this when you have a **username** and **API key** from your firm.

**Endpoint:** `POST https://api.topstepx.com/api/Auth/loginKey`

**Swagger:** `/api/Auth/loginKey` in `https://api.topstepx.com/swagger/index.html`

### Request body

| Field | Type | Description |
|-------|------|-------------|
| `userName` | string | Your username |
| `apiKey` | string | API key from your firm |

### Example

```bash
curl -X POST 'https://api.topstepx.com/api/Auth/loginKey' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -d '{
    "userName": "your_username",
    "apiKey": "your_api_key"
  }'
```

### Success response (shape)

```json
{
  "token": "your_session_token_here",
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

Store `token` securely; it grants access to the Gateway API until expiry.

---

## Authenticate (authorized applications)

Use this for **application** integrations when your firm provides **admin-style** credentials: username, password, `appId`, `verifyKey`, and you supply a **device id**.

**Endpoint:** `POST https://api.topstepx.com/api/Auth/loginApp`

**Swagger:** `/api/Auth/loginApp`

### Request body

| Field | Type | Description |
|-------|------|-------------|
| `userName` | string | Username |
| `password` | string | Password |
| `deviceId` | string | Stable device identifier for your app |
| `appId` | string | Application ID from your firm |
| `verifyKey` | string | Verification key from your firm |

### Example

```bash
curl -X POST 'https://api.topstepx.com/api/Auth/loginApp' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -d '{
    "userName": "yourUsername",
    "password": "yourPassword",
    "deviceId": "yourDeviceId",
    "appId": "yourApplicationID",
    "verifyKey": "yourVerifyKey"
  }'
```

### Success response (shape)

```json
{
  "token": "your_session_token_here",
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

---

## Validate session

When a token is near expiry or after **24 hours**, validate to obtain a **new** token.

**Endpoint:** `POST https://api.topstepx.com/api/Auth/validate`

**Swagger:** `/api/Auth/validate`

Send the request **authenticated** with your current JWT (same pattern as other protected routes).

### Example

```bash
curl -X POST 'https://api.topstepx.com/api/Auth/validate' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

(Response shape matches your client’s Swagger; expect `success` / `errorCode` and a refreshed `token` when applicable.)

---

## Error handling

Responses typically include:

- `success` — boolean
- `errorCode` — numeric code (`0` = success in examples)
- `errorMessage` — optional detail

Always check `success` and `errorCode` before relying on payload data.
