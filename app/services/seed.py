from __future__ import annotations

from app.db import get_connection


BASES = [
    ('Base Central', 1, 4, 'UVI'),
    ('Base Norte', 2, 3, 'SVB'),
    ('Base Sur', 2, 3, 'SVB'),
    ('Retén Logístico', 3, 2, 'LOGISTICO'),
]

PERSONNEL = [
    ('Ana Pérez', 'medico', 'Base Central', 0),
    ('Luis Gómez', 'enfermero', 'Base Central', 0),
    ('Marta Ruiz', 'tecnico', 'Base Central', 1),
    ('Carlos Díaz', 'tecnico', 'Base Central', 1),
    ('Sofía Martín', 'medico', 'Base Norte', 0),
    ('Jorge León', 'enfermero', 'Base Norte', 0),
    ('Paula Sanz', 'tecnico', 'Base Norte', 1),
    ('David Cano', 'tecnico', 'Base Norte', 1),
    ('Lucía Torres', 'medico', 'Base Sur', 0),
    ('Irene Vidal', 'enfermero', 'Base Sur', 0),
    ('Hugo Peña', 'tecnico', 'Base Sur', 1),
    ('Noa Gil', 'tecnico', 'Base Sur', 1),
    ('Raúl Blanco', 'tecnico', 'Retén Logístico', 1),
    ('Elena Mora', 'enfermero', 'Retén Logístico', 0),
]

VEHICLES = [
    ('UVI-01', 'UVI', 'Base Central'),
    ('SVB-11', 'SVB', 'Base Norte'),
    ('SVB-21', 'SVB', 'Base Sur'),
    ('LOG-01', 'LOGISTICO', 'Retén Logístico'),
]


def seed_data() -> None:
    with get_connection() as conn:
        count = conn.execute('SELECT COUNT(*) AS total FROM bases').fetchone()['total']
        if count:
            return

        conn.executemany(
            'INSERT INTO bases(name, priority, min_staff, required_vehicle) VALUES (?, ?, ?, ?)',
            BASES,
        )

        base_map = {
            row['name']: row['id']
            for row in conn.execute('SELECT id, name FROM bases').fetchall()
        }

        conn.executemany(
            'INSERT INTO personnel(full_name, role, home_base_id, is_driver) VALUES (?, ?, ?, ?)',
            [(name, role, base_map[base_name], is_driver) for name, role, base_name, is_driver in PERSONNEL],
        )

        conn.executemany(
            'INSERT INTO vehicles(code, vehicle_type, current_base_id) VALUES (?, ?, ?)',
            [(code, vtype, base_map[base_name]) for code, vtype, base_name in VEHICLES],
        )
