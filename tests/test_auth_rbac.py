import os
import shutil
import tempfile
from app.core.security import hash_password, verify_password, create_jwt_token, decode_jwt_token
from app.models.user import UserCreate, UserRole
from app.storage.user_repository import UserRepository

def test_password_hashing():
    pw = "Admin_123456!"
    h = hash_password(pw)
    assert h.startswith("$scrypt$")
    assert verify_password(pw, h) is True
    assert verify_password("WrongPassword!", h) is False

def test_jwt_tokens():
    secret = "test-secret-key-that-is-at-least-32-chars-long"
    payload = {"sub": "admin", "role": "admin", "name": "Admin"}
    token = create_jwt_token(payload, expires_in_seconds=3600, secret_key=secret)
    assert isinstance(token, str)

    decoded = decode_jwt_token(token, secret_key=secret)
    assert decoded is not None
    assert decoded["sub"] == "admin"
    assert decoded["role"] == "admin"

    # Mauvais secret
    assert decode_jwt_token(token, secret_key="wrong-secret-key-at-least-32-chars-long") is None

    # Token expiré
    expired_token = create_jwt_token(payload, expires_in_seconds=-10, secret_key=secret)
    assert decode_jwt_token(expired_token, secret_key=secret) is None

def test_user_repository():
    tmp_dir = tempfile.mkdtemp()
    tmp_file = os.path.join(tmp_dir, "users_test.json")
    try:
        # Bootstrap default admin
        repo = UserRepository(file_path=tmp_file)
        admin = repo.get_user("admin")
        assert admin is not None
        assert admin.role == UserRole.ADMIN
        assert verify_password("Admin_123456!", admin.password_hash) is True
        assert admin.must_change_password is True

        # List users
        users = repo.list_users()
        assert len(users) == 1
        assert users[0].username == "admin"

        # Create operator
        op_create = UserCreate(
            username="operator1",
            full_name="Pierre Opérateur",
            role=UserRole.OPERATOR,
            password="Operator_123456!"
        )
        op = repo.create_user(op_create)
        assert op.username == "operator1"
        assert op.role == UserRole.OPERATOR

        # Duplicate check
        try:
            repo.create_user(op_create)
            assert False, "Devrait lever une ValueError"
        except ValueError:
            pass

        # Update password
        repo.update_password("operator1", "New_pass_123456!", must_change=False)
        updated_op = repo.get_user("operator1")
        assert verify_password("New_pass_123456!", updated_op.password_hash) is True

        # Last admin protection
        try:
            repo.delete_user("admin")
            assert False, "Ne doit pas autoriser la suppression du dernier admin"
        except ValueError:
            pass

        # Delete operator
        assert repo.delete_user("operator1") is True
        assert repo.get_user("operator1") is None
        assert len(repo.list_users()) == 1
    finally:
        shutil.rmtree(tmp_dir)

if __name__ == "__main__":
    print("Running test_password_hashing...")
    test_password_hashing()
    print("Running test_jwt_tokens...")
    test_jwt_tokens()
    print("Running test_user_repository...")
    test_user_repository()
    print("All security and RBAC unit tests passed successfully!")
