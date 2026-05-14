import psycopg2

# Tu URL de Render
DB_URL = "postgresql://motoclub_fr5u_user:0jpM3SOgBUgXjssRQU7MqDum301c8jaS@dpg-d82fv672gups73c46tc0-a.oregon-postgres.render.com/motoclub_fr5u"

def crear_base_de_datos():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        tablas_sql = """
        CREATE TABLE IF NOT EXISTS brands (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL
        );

        CREATE TABLE IF NOT EXISTS models (
            id SERIAL PRIMARY KEY,
            brand_id INTEGER REFERENCES brands(id),
            name VARCHAR(100) NOT NULL,
            year INTEGER,
            price NUMERIC(10, 2)
        );
        """
        cur.execute(tablas_sql)
        conn.commit()
        print("¡Éxito! Las tablas han sido creadas en Render.")
        cur.close()
        conn.close()
    except Exception as error:
        print(f"Hubo un error: {error}")

if __name__ == "__main__":
    crear_base_de_datos()