# Test-only scripts

## Provision an isolated browser-audit administrator

`provision_test_admin.py` is a manual, test-only utility. It loads the repository
root `.env.test` and aborts unless both database URLs target
`collab_matcher_test` on localhost port `5435`. It then confirms the live
database identity before writing one temporary ADMIN user. It does not expose
an HTTP endpoint and is never run during application startup.

Run it from the repository root with an explicit confirmation and a local
credential-file path:

```powershell
.\.venv\Scripts\python.exe backend\scripts\provision_test_admin.py `
  --confirm-test-db `
  --credentials-file "$env:USERPROFILE\.copilot\session-state\<session-id>\files\admin-test-account.json"
```

The script generates a temporary password, stores it only in the specified
user-restricted local file, and does not print it. Use the same file with
`--cleanup` after testing to remove only that temporary ADMIN account. Do not
use this utility with the normal application database or commit the credential
file.
