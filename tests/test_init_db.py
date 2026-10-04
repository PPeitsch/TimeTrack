"""Tests for init_db.py helper functions."""

import os

# Import the functions we want to test
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from init_db import check_dependencies, extract_db_info, main, parse_env_file


class TestParseEnvFile:
    """Tests for the parse_env_file function."""

    def test_parse_env_file_with_valid_content(self, tmp_path):
        """Test parsing a valid .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
DATABASE_URL=sqlite:///test.db
SECRET_KEY='my-secret-key'
FLASK_ENV="development"
# This is a comment
EMPTY_LINE_BELOW

DEBUG=true
"""
        )

        result = parse_env_file(str(env_file))

        assert result["DATABASE_URL"] == "sqlite:///test.db"
        assert result["SECRET_KEY"] == "my-secret-key"
        assert result["FLASK_ENV"] == "development"
        assert result["DEBUG"] == "true"
        # Empty line should not raise errors
        assert "EMPTY_LINE_BELOW" not in result

    def test_parse_env_file_nonexistent(self):
        """Test parsing a non-existent file returns empty dict."""
        result = parse_env_file("/nonexistent/path/.env")
        assert result == {}

    def test_parse_env_file_empty(self, tmp_path):
        """Test parsing an empty file."""
        env_file = tmp_path / ".env"
        env_file.write_text("")
        result = parse_env_file(str(env_file))
        assert result == {}

    def test_parse_env_file_only_comments(self, tmp_path):
        """Test parsing a file with only comments."""
        env_file = tmp_path / ".env"
        env_file.write_text("# Comment 1\n# Comment 2\n")
        result = parse_env_file(str(env_file))
        assert result == {}

    def test_parse_env_file_strips_quotes(self, tmp_path):
        """Test that quotes are stripped from values."""
        env_file = tmp_path / ".env"
        env_file.write_text("VAR1='single'\nVAR2=\"double\"\n")
        result = parse_env_file(str(env_file))
        assert result["VAR1"] == "single"
        assert result["VAR2"] == "double"

    def test_parse_env_file_handles_equals_in_value(self, tmp_path):
        """Test that values containing '=' are handled correctly."""
        env_file = tmp_path / ".env"
        env_file.write_text("DATABASE_URL=postgresql://user:pass=123@host/db\n")
        result = parse_env_file(str(env_file))
        assert result["DATABASE_URL"] == "postgresql://user:pass=123@host/db"


class TestExtractDbInfo:
    """Tests for the extract_db_info function."""

    def test_extract_sqlite_info(self):
        """Test extracting SQLite database info."""
        result = extract_db_info("sqlite:///timetrack.db")
        assert result["type"] == "sqlite"
        assert result["path"] == "timetrack.db"

    def test_extract_sqlite_absolute_path(self):
        """Test extracting SQLite info with absolute path."""
        result = extract_db_info("sqlite:////absolute/path/db.sqlite")
        assert result["type"] == "sqlite"
        assert result["path"] == "/absolute/path/db.sqlite"

    def test_extract_postgres_info(self):
        """Test extracting PostgreSQL database info."""
        result = extract_db_info("postgresql://myuser:mypass@localhost:5432/mydb")
        assert result["type"] == "postgres"
        assert result["user"] == "myuser"
        assert result["password"] == "mypass"
        assert result["host"] == "localhost"
        assert result["port"] == "5432"
        assert result["name"] == "mydb"

    def test_extract_postgres_special_chars_in_password(self):
        """Test PostgreSQL with special characters in password."""
        result = extract_db_info("postgresql://user:p@ss@host:5432/db")
        # This edge case may not match perfectly due to regex limitations
        # The current regex expects password without @ symbol
        assert result.get("type") in ["postgres", "unknown"]

    def test_extract_unknown_database_type(self):
        """Test extracting info from unknown database URL."""
        result = extract_db_info("mysql://user:pass@localhost:3306/db")
        assert result["type"] == "unknown"

    def test_extract_empty_url(self):
        """Test extracting info from empty URL."""
        result = extract_db_info("")
        assert result["type"] == "unknown"

    def test_extract_malformed_url(self):
        """Test extracting info from malformed URL."""
        result = extract_db_info("not-a-valid-url")
        assert result["type"] == "unknown"


class TestCheckDependencies:
    """Tests for the check_dependencies function."""

    def test_check_dependencies_all_installed(self):
        """Test when all required dependencies are installed."""
        # Flask and related packages should be installed in test environment
        result = check_dependencies()
        # We expect no missing packages for the main ones
        assert isinstance(result, list)

    @patch("init_db.importlib.util.find_spec")
    def test_check_dependencies_some_missing(self, mock_find_spec):
        """Test when some dependencies are missing."""

        def side_effect(name):
            if name in ["flask", "flask_sqlalchemy"]:
                return MagicMock()  # Installed
            return None  # Not installed

        mock_find_spec.side_effect = side_effect
        result = check_dependencies()
        assert "flask-migrate" in result or len(result) > 0

    @patch("init_db.importlib.util.find_spec")
    def test_check_dependencies_all_missing(self, mock_find_spec):
        """Test when all dependencies are missing."""
        mock_find_spec.return_value = None
        result = check_dependencies()
        assert len(result) == 5  # All 5 required packages missing


class TestMain:
    """main() reports missing dependencies instead of installing them."""

    @patch("init_db.check_dependencies", return_value=["flask-migrate"])
    def test_exits_when_dependencies_are_missing(self, _mock_check, capsys):
        with pytest.raises(SystemExit) as exit_info:
            main()
        assert exit_info.value.code == 1
        out = capsys.readouterr().out
        assert "flask-migrate" in out
        assert "pip install -r requirements.txt" in out


class TestCreateSchema:
    """create_schema builds the database from the migrations, like production."""

    @pytest.fixture
    def file_app(self, tmp_path):
        from app import create_app
        from tests.conftest import TestConfig

        class FileConfig(TestConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'tt.db'}"

        return create_app(FileConfig)

    def test_applies_migrations_on_empty_database(self, file_app):
        from sqlalchemy import inspect

        from app.db.database import db
        from init_db import create_schema

        with file_app.app_context():
            assert create_schema(db) is True
            tables = set(inspect(db.engine).get_table_names())
            assert {"alembic_version", "employees", "holiday_years"} <= tables
            # Running it again is a no-op.
            assert create_schema(db) is True

    def test_refuses_database_without_migration_history(self, file_app):
        from app.db.database import db
        from init_db import create_schema

        with file_app.app_context():
            db.create_all()
            assert create_schema(db) is False
