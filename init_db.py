import getpass
import importlib.util
import os
import re
import subprocess
import sys
import time
from pathlib import Path


def parse_env_file(file_path):
    """Parse an env file and return a dictionary of key-value pairs."""
    env_vars = {}
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        key, value = parts
                        env_vars[key] = value
    return env_vars


def extract_db_info(db_url):
    """Extract database connection info from a DATABASE_URL string."""
    # For SQLite
    if db_url.startswith("sqlite:///"):
        return {"type": "sqlite", "path": db_url.replace("sqlite:///", "")}

    # For PostgreSQL
    match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", db_url)
    if match:
        return {
            "type": "postgres",
            "user": match.group(1),
            "password": match.group(2),
            "host": match.group(3),
            "port": match.group(4),
            "name": match.group(5),
        }

    # Default empty response if format not recognized
    return {"type": "unknown"}


def initialize_database_manually():
    """Initialize database tables using direct Python imports."""
    try:
        print("\nIntentando inicializar la base de datos directamente...")

        # Import the application
        sys.path.append(os.getcwd())

        # Try to import the necessary modules
        try:
            from app import create_app
            from app.config.config import Config
            from app.db.database import db

            print("✓ Módulos importados correctamente")
        except ImportError as e:
            print(f"❌ Error al importar módulos: {e}")
            return False, f"Error al importar: {e}"

        # Create the app with Config
        try:
            app = create_app(Config)
            print("✓ Aplicación creada correctamente")
        except Exception as e:
            print(f"❌ Error al crear la aplicación: {e}")
            return False, f"Error al crear app: {e}"

        # Create tables
        try:
            with app.app_context():
                db.create_all()
                print("✓ Tablas creadas correctamente")

            print("\nLa base de datos ha sido inicializada exitosamente.")
            return True, "Base de datos inicializada correctamente"
        except Exception as e:
            print(f"❌ Error al crear tablas: {e}")
            return False, f"Error al crear tablas: {e}"

    except Exception as e:
        print(f"❌ Error durante la inicialización manual: {e}")
        return False, str(e)


def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = ["flask", "flask-sqlalchemy", "flask-migrate"]
    missing_packages = []

    for package in required_packages:
        spec = importlib.util.find_spec(package.replace("-", "_"))
        if spec is None:
            missing_packages.append(package)

    return missing_packages


def install_missing_packages(packages):
    """Install missing packages."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    print("=== Inicialización de base de datos para TimeTrack ===")

    # Check dependencies
    missing_packages = check_dependencies()
    if missing_packages:
        print(
            f"\n⚠️ Se encontraron dependencias faltantes: {', '.join(missing_packages)}"
        )
        install = input("¿Instalar dependencias faltantes? (s/n) [s]: ").lower() != "n"
        if install:
            print("Instalando dependencias...")
            if install_missing_packages(missing_packages):
                print("✓ Dependencias instaladas correctamente")
            else:
                print("❌ Error al instalar dependencias")
                return
        else:
            print("❌ No se pueden continuar sin las dependencias necesarias")
            return

    # Check if .env exists
    env_path = ".env"
    env_example_path = ".env.example"

    if os.path.exists(env_path):
        print(f"Se encontró el archivo {env_path} existente.")
        env_vars = parse_env_file(env_path)
        using_existing = True
    elif os.path.exists(env_example_path):
        print(f"No se encontró {env_path}, usando {env_example_path} como plantilla.")
        env_vars = parse_env_file(env_example_path)
        using_existing = False
    else:
        print(f"No se encontraron archivos de configuración. Se creará uno nuevo.")
        env_vars = {
            "DATABASE_URL": "sqlite:///timetrack.db",
            "SECRET_KEY": "desarrollo-local-seguro",
            "FLASK_APP": 'app:create_app("app.config.config.Config")',
            "FLASK_ENV": "development",
            "FLASK_DEBUG": "1",
        }
        using_existing = False

    # Set correct FLASK_APP with factory arguments
    if (
        "FLASK_APP" not in env_vars
        or "create_app" not in env_vars["FLASK_APP"]
        or "(" not in env_vars["FLASK_APP"]
    ):
        env_vars["FLASK_APP"] = 'app:create_app("app.config.config.Config")'
        print(
            "\n✓ Se ha actualizado la configuración de FLASK_APP para usar la factory function correctamente"
        )

    # Extract current database configuration
    db_url = env_vars.get("DATABASE_URL", "")
    db_info = extract_db_info(db_url)

    # Ask user if they want to modify the configuration
    if using_existing:
        print("\nConfiguración actual:")
        if db_info["type"] == "sqlite":
            print(f"Tipo de base de datos: SQLite")
            print(f"Ruta del archivo: {db_info['path']}")
        elif db_info["type"] == "postgres":
            print(f"Tipo de base de datos: PostgreSQL")
            print(f"Nombre de la base de datos: {db_info['name']}")
            print(f"Usuario: {db_info['user']}")
            print(f"Host: {db_info['host']}:{db_info['port']}")

        modify = (
            input(
                "\n¿Deseas modificar la configuración de la base de datos? (s/n) [n]: "
            ).lower()
            == "s"
        )
    else:
        modify = True

    if modify:
        # Ask for database type
        print("\nSelecciona el tipo de base de datos:")
        db_type = (
            input("¿PostgreSQL o SQLite? (postgres/sqlite) [sqlite]: ").lower()
            or "sqlite"
        )

        if db_type == "sqlite":
            # Configure SQLite
            sqlite_path = (
                input(f"Ruta del archivo SQLite [timetrack.db]: ") or "timetrack.db"
            )
            env_vars["DATABASE_URL"] = f"sqlite:///{sqlite_path}"
            db_info = extract_db_info(env_vars["DATABASE_URL"])

            print("\nBase de datos SQLite configurada.")

        elif db_type == "postgres":
            # Configure PostgreSQL
            db_name = input("Nombre de la base de datos [timetrack]: ") or "timetrack"
            db_user = input("Usuario de PostgreSQL [postgres]: ") or "postgres"
            db_pass = getpass.getpass("Contraseña para PostgreSQL: ")
            db_host = input("Host de PostgreSQL [localhost]: ") or "localhost"
            db_port = input("Puerto de PostgreSQL [5432]: ") or "5432"

            env_vars["DATABASE_URL"] = (
                f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            )
            db_info = extract_db_info(env_vars["DATABASE_URL"])

        else:
            print(f"Tipo de base de datos no reconocido: {db_type}")
            return

    # Check if SECRET_KEY needs to be modified
    modify_secret = (
        input("\n¿Deseas modificar la SECRET_KEY? (s/n) [n]: ").lower() == "s"
    )
    if modify_secret:
        import secrets

        new_secret = secrets.token_hex(16)
        use_generated = (
            input(
                f"¿Usar clave generada automáticamente ({new_secret})? (s/n) [s]: "
            ).lower()
            != "n"
        )

        if use_generated:
            env_vars["SECRET_KEY"] = new_secret
        else:
            custom_secret = input("Ingresa tu SECRET_KEY personalizada: ")
            env_vars["SECRET_KEY"] = custom_secret

    # Save the environment variables to .env
    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

    print(
        f"\nArchivo {env_path} {'actualizado' if using_existing else 'creado'} correctamente."
    )

    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value

    # Initialize database directly (without using flask db commands)
    success, message = initialize_database_manually()

    if success:
        print("\n✅ Configuración completada exitosamente")
        print("Ahora puedes ejecutar 'flask run' para iniciar la aplicación.")
    else:
        print(f"\n❌ Error al inicializar la base de datos: {message}")
        print("\nPuedes intentar ejecutar estos comandos manualmente para depurar:")
        print(
            f"1. Asegúrate de tener FLASK_APP configurado como: {env_vars.get('FLASK_APP')}"
        )
        print("2. Verifica que Flask-Migrate está instalado: pip install flask-migrate")
        print("3. Ejecuta: flask db init")
        print("4. Ejecuta: flask db migrate -m 'Initial migration'")
        print("5. Ejecuta: flask db upgrade")


if __name__ == "__main__":
    main()
