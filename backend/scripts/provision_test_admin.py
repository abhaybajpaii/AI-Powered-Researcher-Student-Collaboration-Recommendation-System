"""Test-only provisioning for an isolated browser-audit administrator.

This command never uses the application startup path or public HTTP API. It
requires an explicit confirmation, validates both configured URLs and the live
database identity, and stores the generated temporary credentials in a
user-restricted local file. Use --cleanup with the same file to remove only
the temporary account created here.
"""

import argparse
import asyncio
import getpass
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from typing import Dict
from uuid import uuid4

from sqlalchemy import func, select, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


EXPECTED_HOSTS = {"localhost", "127.0.0.1"}
EXPECTED_PORT = 5435
EXPECTED_DATABASE = "collab_matcher_test"
TEST_ADMIN_PREFIX = "phase5310-admin-"


def _read_env_file(path: Path) -> Dict[str, str]:
    if not path.is_file():
        raise ValueError("The required .env.test file was not found.")

    values: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def validate_test_database_target(values: Dict[str, str]) -> URL:
    required = ("DATABASE_URL", "DATABASE_SYNC_URL", "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB")
    if any(not values.get(key) for key in required):
        raise ValueError(".env.test is missing a required database setting.")

    if (
        values["POSTGRES_HOST"] not in EXPECTED_HOSTS
        or values["POSTGRES_PORT"] != str(EXPECTED_PORT)
        or values["POSTGRES_DB"] != EXPECTED_DATABASE
    ):
        raise ValueError(".env.test does not target the approved isolated test database.")

    async_url = make_url(values["DATABASE_URL"])
    sync_url = make_url(values["DATABASE_SYNC_URL"])
    for url in (async_url, sync_url):
        if (
            not url.drivername.startswith("postgresql")
            or url.host not in EXPECTED_HOSTS
            or url.port != EXPECTED_PORT
            or url.database != EXPECTED_DATABASE
        ):
            raise ValueError("Both configured database URLs must target localhost:5435/collab_matcher_test.")
    if not values.get("POSTGRES_USER") or not values.get("POSTGRES_PASSWORD"):
        raise ValueError(".env.test is missing PostgreSQL credentials.")
    return async_url


def _restrict_credentials_file(path: Path) -> None:
    if os.name == "nt":
        username = subprocess.check_output(
            ["whoami"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        subprocess.run(
            [
                "icacls",
                str(path),
                "/inheritance:r",
                "/grant:r",
                f"{username}:(F)",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    else:
        path.chmod(0o600)


def _load_or_create_credentials(path: Path) -> tuple[dict, bool]:
    if path.exists():
        _restrict_credentials_file(path)
        credentials = json.loads(path.read_text(encoding="utf-8"))
        if not (
            isinstance(credentials, dict)
            and credentials.get("email", "").startswith(TEST_ADMIN_PREFIX)
            and credentials.get("email", "").endswith("@example.com")
            and credentials.get("password")
        ):
            raise ValueError("The credential file is not for this test-only provisioner.")
        return credentials, False

    credentials = {
        "email": f"{TEST_ADMIN_PREFIX}{uuid4().hex}@example.com",
        "password": secrets.token_urlsafe(32),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as file:
        json.dump(credentials, file)
    try:
        _restrict_credentials_file(path)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return credentials, True


async def _run(args: argparse.Namespace) -> str:
    root = Path(__file__).resolve().parents[2]
    env_values = _read_env_file(root / ".env.test")
    database_url = validate_test_database_target(env_values)

    # Ensure imported application settings cannot fall back to the normal .env.
    os.environ.update(env_values)
    sys.path.insert(0, str(root))

    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            database_name = await connection.scalar(text("SELECT current_database()"))
            if database_name != EXPECTED_DATABASE:
                raise ValueError("The live connection is not to the approved test database.")

        from backend.app.core.security import get_password_hash
        from backend.app.db.base import Base  # noqa: F401 - register related models
        from backend.app.models.faculty import Faculty
        from backend.app.models.student import Student
        from backend.app.models.user import User

        sessions = async_sessionmaker(engine, expire_on_commit=False)
        credentials_path = Path(args.credentials_file)
        if credentials_path.is_symlink():
            raise ValueError("The credential file must not be a symbolic link.")
        credentials_path = credentials_path.resolve()
        if args.cleanup:
            if not credentials_path.is_file():
                return "No temporary credential file exists; nothing to clean up."
            credentials = json.loads(credentials_path.read_text(encoding="utf-8"))
            email = credentials.get("email", "")
            if not (
                email.startswith(TEST_ADMIN_PREFIX)
                and email.endswith(("@example.com", "@example.invalid"))
            ):
                raise ValueError("Refusing cleanup for an account outside the temporary test namespace.")

            async with sessions() as session:
                user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
                if user is None:
                    return "The temporary account is already absent."
                if user.role != "ADMIN" or not user.is_active:
                    raise ValueError("Refusing to remove an account that is not the expected active test ADMIN.")
                student_count = await session.scalar(
                    select(func.count(Student.id)).where(Student.user_id == user.id)
                )
                faculty_count = await session.scalar(
                    select(func.count(Faculty.id)).where(Faculty.user_id == user.id)
                )
                if student_count or faculty_count:
                    raise ValueError("Refusing cleanup because the account has an attached profile.")
                await session.delete(user)
                await session.commit()
            return "The temporary ADMIN account was removed."

        credentials, _ = _load_or_create_credentials(credentials_path)
        async with sessions() as session:
            user = (
                await session.execute(select(User).where(User.email == credentials["email"]))
            ).scalar_one_or_none()
            if user is not None:
                if user.role != "ADMIN" or not user.is_active:
                    raise ValueError("The generated account address is already assigned to a different account.")
                return "The temporary ADMIN account already exists; no account changes were made."

            session.add(
                User(
                    email=credentials["email"],
                    hashed_password=get_password_hash(credentials["password"]),
                    role="ADMIN",
                    is_active=True,
                )
            )
            await session.commit()
        return "The temporary ADMIN account was created in collab_matcher_test."
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision or clean up a test-only ADMIN in collab_matcher_test.")
    parser.add_argument(
        "--confirm-test-db",
        action="store_true",
        required=True,
        help="Explicitly confirm that only collab_matcher_test on host port 5435 may be used.",
    )
    parser.add_argument(
        "--credentials-file",
        required=True,
        help="User-private local JSON file used to retain the temporary login for browser testing.",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove only the temporary ADMIN account referenced by the credentials file.",
    )
    args = parser.parse_args()
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        message = asyncio.run(_run(args))
    except Exception as exc:
        print(f"Test-admin operation aborted: {exc}", file=sys.stderr)
        return 1
    print(message)
    if not args.cleanup:
        print("Temporary credentials were stored in the specified protected local file; they are not printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
