# External image API providers

API keys are stored as Generic Credentials in Windows Credential Manager. Provider JSON contains only endpoint/model/credential target.

```powershell
python -m backend.cli credentials set openai
python -m backend.cli credentials check openai
python -m backend.cli credentials delete openai
```
`set` uses a hidden `getpass` prompt, so the key does not enter PowerShell history.

Supported mappings:
- OpenAI-compatible/Together: `data[0].b64_json` or `data[0].url`.
- Stability AI v2: multipart request; accepts raw image response or JSON base64.
- Replicate: prediction creation, polling and URL/list output.

Copy `config/image-providers.example.json` to user app-data and customize endpoints. Never commit the real key.
