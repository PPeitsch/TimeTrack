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
                        env_vars[key] = value.strip("'\"")
    return env_vars


def extract_db_info(db_url):
    """Extract database connection info from a DATABASE_URL string."""
    if db_url.startswith("sqlite:///"):
        return {"type": "sqlite", "path": db_url.replace("sqlite:///", "")}

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
    return {"type": "unknown"}


def initialize_database_manually():
    """Initialize database tables using direct Python imports."""
    app = None
    try:
        print("\nIntentando inicializar la base de datos directamente...")
        sys.path.append(os.getcwd())

        from app import create_app
        from app.config.config import Config
        from app.db.database import db
        from app.models.models import Holiday
        from app.services.holiday_service import get_holiday_provider
        from app.utils.init_data import init_data  # Import the data seeder

        print("✓ Módulos importados correctamente")

        app = create_app(Config)
        print("✓ Aplicación creada correctamente")

        with app.app_context():
            db.create_all()
            print("✓ Tablas creadas correctamente")

            # Populate initial data (absence codes, default employee)
            init_data()
            print("✓ Datos iniciales (códigos de ausencia) poblados.")

            populate = (
                input(
                    "\n¿Deseas poblar la base de datos con los feriados? (s/n) [s]: "
                ).lower()
                != "n"
            )
            if populate:
                print("Obteniendo proveedor de feriados...")
                provider = get_holiday_provider(Config)
                current_year = time.localtime().tm_year
                years_to_fetch = [current_year, current_year + 1]

                print(f"Obteniendo feriados para los años {years_to_fetch}...")
                all_holidays = []
                for year in years_to_fetch:
                    holidays = provider.get_holidays(year)
                    if holidays:
                        print(f"✓ Se encontraron {len(holidays)} feriados para {year}")
                        all_holidays.extend(holidays)
                    else:
                        print(f"⚠️ No se encontraron feriados para {year}.")

                if all_holidays:
                    unique_holidays = {h.date: h for h in all_holidays}.values()

                    db.session.query(Holiday).delete()
                    db.session.commit()

                    db.session.bulk_save_objects(list(unique_holidays))
                    db.session.commit()
                    print(f"✓ {len(unique_holidays)} feriados únicos guardados.")

        print("\nLa base de datos ha sido inicializada exitosamente.")
        return True, "Base de datos inicializada correctamente"

    except Exception as e:
        error_message = f"Error durante la inicialización manual: {e}"
        print(f"❌ {error_message}")
        if app:
            with app.app_context():
                if db.session.is_active:
                    db.session.rollback()
                    print("✓ Rollback de la sesión de base de datos realizado.")
        return False, str(e)


def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = {
        "flask": "flask",
        "flask-sqlalchemy": "flask_sqlalchemy",
        "flask-migrate": "flask_migrate",
        "requests": "requests",
        "beautifulsoup4": "bs4",
    }
    missing_packages = []
    for pip_name, import_name in required_packages.items():
        if importlib.util.find_spec(import_name) is None:
            missing_packages.append(pip_name)
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

    missing_packages = check_dependencies()
    if missing_packages:
        print(
            f"\n⚠️ Se encontraron dependencias faltantes: {', '.join(missing_packages)}"
        )
        install = input("¿Instalar dependencias faltantes? (s/n) [s]: ").lower() != "n"
        if install:
            print("Instalando dependencias...")
            if not install_missing_packages(missing_packages):
                print("❌ Error al instalar dependencias.")
                return
            print("✓ Dependencias instaladas correctamente")

    env_path = ".env"
    env_example_path = ".env.example"
    using_existing = False
    if os.path.exists(env_path):
        print(f"\nSe encontró el archivo {env_path} existente.")
        env_vars = parse_env_file(env_path)
        using_existing = True
    elif os.path.exists(env_example_path):
        print(f"No se encontró {env_path}, usando {env_example_path} como plantilla.")
        env_vars = parse_env_file(env_example_path)
    else:
        print("No se encontraron archivos de configuración. Se creará uno nuevo.")
        env_vars = {
            "DATABASE_URL": "sqlite:///timetrack.db",
            "SECRET_KEY": "desarrollo-local-seguro",
            "FLASK_APP": "run.py",
            "FLASK_ENV": "development",
            "FLASK_DEBUG": "1",
            "FLASK_DEBUG": "1",
            "HOLIDAY_PROVIDER": "ARGENTINA_API",
            "HOLIDAYS_BASE_URL": "https://www.argentina.gob.ar/jefatura/feriados-nacionales-{year}",
            "HOLIDAY_API_URL": "https://api.argentinadatos.com/v1/feriados/{year}",
        }

    if "FLASK_APP" not in env_vars or "run.py" not in env_vars.get("FLASK_APP", ""):
        env_vars["FLASK_APP"] = "run.py"
        print("\n✓ Se ha actualizado la configuración de FLASK_APP para usar run.py")

    db_url = env_vars.get("DATABASE_URL", "")
    db_info = extract_db_info(db_url)

    if using_existing:
        print("\nConfiguración actual:")
        print(f"  Base de datos: {db_info.get('type', 'desconocido')}")
        print(
            f"  Proveedor de feriados: {env_vars.get('HOLIDAY_PROVIDER', 'No configurado')}"
        )
        modify = (
            input("\n¿Deseas modificar la configuración? (s/n) [n]: ").lower() == "s"
        )
    else:
        modify = True

    if modify:
        print("\nSelecciona el tipo de base de datos:")
        print("  1. SQLite (default)")
        print("  2. PostgreSQL")
        db_choice = ""
        while db_choice not in ["1", "2"]:
            db_choice = input("Selecciona una opción [1]: ").strip() or "1"

        if db_choice == "1":
            sqlite_path = (
                input("Ruta del archivo SQLite [timetrack.db]: ") or "timetrack.db"
            )
            env_vars["DATABASE_URL"] = f"sqlite:///{sqlite_path}"
        else:
            db_name = input("Nombre de la base de datos [timetrack]: ") or "timetrack"
            db_user = input("Usuario de PostgreSQL [postgres]: ") or "postgres"
            db_pass = getpass.getpass("Contraseña para PostgreSQL: ")
            db_host = input("Host de PostgreSQL [localhost]: ") or "localhost"
            db_port = input("Puerto de PostgreSQL [5432]: ") or "5432"
            env_vars["DATABASE_URL"] = (
                f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            )

    modify_secret = (
        input("\n¿Deseas modificar la SECRET_KEY? (s/n) [n]: ").lower() == "s"
    )
    if modify_secret:
        import secrets

        new_secret = secrets.token_hex(16)
        use_generated = input(f"¿Usar clave generada? (s/n) [s]: ").lower() != "n"
        env_vars["SECRET_KEY"] = (
            new_secret if use_generated else input("Ingresa tu SECRET_KEY: ")
        )

    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

    print(f"\nArchivo {env_path} {'actualizado' if using_existing else 'creado'}.")

    for key, value in env_vars.items():
        os.environ[key] = value

    success, message = initialize_database_manually()

    if success:
        print("\n✅ Configuración completada exitosamente.")
        print("Ahora puedes ejecutar 'flask run' para iniciar la aplicación.")
    else:
        print(f"\n❌ Error al inicializar la base de datos: {message}")
        print("\nPuedes intentar ejecutar estos comandos manualmente para depurar:")
        print("1. flask db init")
        print("2. flask db migrate -m 'Initial migration'")
        print("3. flask db upgrade")


if __name__ == "__main__":
    main()
