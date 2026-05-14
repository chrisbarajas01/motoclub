import os
import psycopg2

# Obtener la URL de la base de datos desde variables de entorno
DB_URL = os.environ.get('DATABASE_URL', 'postgresql://motoclub_fr5u_user:0jpM3SOgBUgXjssRQU7MqDum301c8jaS@dpg-d82fv672gups73c46tc0-a.oregon-postgres.render.com/motoclub_fr5u')

def crear_base_de_datos():
    if not DB_URL:
        print("Error: No se encontró la variable de entorno DATABASE_URL")
        return

    try:
        print("Conectando a la base de datos...")
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        print("Creando tablas...")

        # Crear tabla de marcas
        cur.execute("""
        CREATE TABLE IF NOT EXISTS brands (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE
        );
        """)

        # Crear tabla de modelos
        cur.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id SERIAL PRIMARY KEY,
            brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            year INTEGER CHECK (year >= 1900 AND year <= 2100),
            price NUMERIC(10, 2) CHECK (price >= 0),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        conn.commit()
        print("¡Éxito! Las tablas han sido creadas en Render.")
        cur.close()
        conn.close()

    except psycopg2.Error as error:
        print(f"Error de base de datos: {error}")
    except Exception as error:
        print(f"Error general: {error}")

if __name__ == "__main__":
    crear_base_de_datos()