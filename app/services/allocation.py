from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from app.db import get_connection


@dataclass
class RebalanceResult:
    summary: str
    moves: list[str]


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat()


def _role_priority(role: str) -> int:
    order = {'medico': 0, 'enfermero': 1, 'tecnico': 2}
    return order.get(role, 99)


def _choose_vehicle(required_vehicle: str, staff_roles: Iterable[str]) -> str:
    roles = set(staff_roles)
    if 'medico' in roles and 'enfermero' in roles:
        return 'UVI'
    if required_vehicle == 'LOGISTICO':
        return 'LOGISTICO'
    return 'SVB'


def find_replacement_for_person(person_id: int) -> dict | None:
    with get_connection() as conn:
        target = conn.execute(
            '''
            SELECT p.id, p.full_name, p.role, p.home_base_id, b.priority AS home_priority, b.name AS base_name
            FROM personnel p
            JOIN bases b ON b.id = p.home_base_id
            WHERE p.id = ?
            ''',
            (person_id,),
        ).fetchone()
        if not target:
            return None

        replacement = conn.execute(
            '''
            SELECT p.id, p.full_name, p.role, b.name AS base_name, b.priority
            FROM personnel p
            JOIN bases b ON b.id = p.home_base_id
            WHERE p.role = ? AND p.status = 'available' AND p.id != ?
            ORDER BY b.priority DESC, p.is_driver DESC, p.full_name ASC
            LIMIT 1
            ''',
            (target['role'], target['id']),
        ).fetchone()

        return dict(replacement) if replacement else None


def record_absence(full_name: str, reason: str, reported_by: str) -> dict:
    with get_connection() as conn:
        person = conn.execute(
            'SELECT id, full_name, role FROM personnel WHERE lower(full_name) = lower(?)',
            (full_name.strip(),),
        ).fetchone()
        if not person:
            return {'ok': False, 'message': f'No encontré a {full_name} en la dotación.'}

        conn.execute(
            "UPDATE personnel SET status = 'absent' WHERE id = ?",
            (person['id'],),
        )

        replacement = find_replacement_for_person(person['id'])
        replacement_id = replacement['id'] if replacement else None

        conn.execute(
            '''
            INSERT INTO absences(person_id, reason, created_at, reported_by, replacement_person_id)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (person['id'], reason, now_iso(), reported_by, replacement_id),
        )

    rebalance = rebalance_staff()
    replacement_text = (
        f"Reemplazo sugerido: {replacement['full_name']} ({replacement['role']}) desde {replacement['base_name']}."
        if replacement
        else 'No hay reemplazo directo disponible ahora mismo.'
    )
    return {
        'ok': True,
        'message': (
            f"Ausencia registrada: {person['full_name']} ({person['role']}).\n"
            f"Motivo: {reason}.\n{replacement_text}\n\n{rebalance.summary}"
        ),
    }


def register_alert(description: str, location: str, source: str = 'telegram') -> str:
    with get_connection() as conn:
        conn.execute(
            'INSERT INTO alerts(source, description, location, created_at) VALUES (?, ?, ?, ?)',
            (source, description, location, now_iso()),
        )
    return f'Alerta registrada en {location}: {description}'


def rebalance_staff() -> RebalanceResult:
    moves: list[str] = []
    with get_connection() as conn:
        conn.execute('UPDATE assignments SET active = 0 WHERE active = 1')

        available_people = conn.execute(
            '''
            SELECT p.id, p.full_name, p.role, p.is_driver, b.name AS home_base_name, b.priority AS home_priority
            FROM personnel p
            JOIN bases b ON b.id = p.home_base_id
            WHERE p.status = 'available'
            ORDER BY b.priority ASC, CASE p.role WHEN 'medico' THEN 0 WHEN 'enfermero' THEN 1 ELSE 2 END, p.full_name ASC
            '''
        ).fetchall()
        available = [dict(row) for row in available_people]

        bases = conn.execute(
            'SELECT id, name, priority, min_staff, required_vehicle FROM bases ORDER BY priority ASC, name ASC'
        ).fetchall()

        vehicles = [dict(v) for v in conn.execute(
            "SELECT id, code, vehicle_type, current_base_id FROM vehicles WHERE status = 'available'"
        ).fetchall()]

        assigned_person_ids: set[int] = set()
        assigned_vehicle_ids: set[int] = set()

        for base in bases:
            base_staff: list[dict] = []
            for person in available:
                if person['id'] in assigned_person_ids:
                    continue
                if len(base_staff) >= base['min_staff']:
                    break
                base_staff.append(person)
                assigned_person_ids.add(person['id'])
                if person['home_base_name'] != base['name']:
                    moves.append(f"{person['full_name']} -> {base['name']}")

            staff_roles = [p['role'] for p in base_staff]
            expected_vehicle = _choose_vehicle(base['required_vehicle'], staff_roles)
            vehicle = next(
                (
                    v for v in vehicles
                    if v['id'] not in assigned_vehicle_ids and v['vehicle_type'] == expected_vehicle
                ),
                None,
            )
            if vehicle is None:
                vehicle = next((v for v in vehicles if v['id'] not in assigned_vehicle_ids), None)
            if vehicle:
                assigned_vehicle_ids.add(vehicle['id'])

            for person in base_staff:
                conn.execute(
                    '''
                    INSERT INTO assignments(base_id, person_id, vehicle_id, assigned_at, active)
                    VALUES (?, ?, ?, ?, 1)
                    ''',
                    (base['id'], person['id'], vehicle['id'] if vehicle else None, now_iso()),
                )

        uncovered = []
        for base in bases:
            assigned_count = conn.execute(
                'SELECT COUNT(*) AS total FROM assignments WHERE base_id = ? AND active = 1',
                (base['id'],),
            ).fetchone()['total']
            if assigned_count < base['min_staff']:
                uncovered.append(f"{base['name']} ({assigned_count}/{base['min_staff']})")

    summary = 'Reorganización completada.'
    if uncovered:
        summary += ' Bases por debajo del mínimo: ' + ', '.join(uncovered) + '.'
    else:
        summary += ' Todas las bases quedaron cubiertas al mínimo operativo.'
    return RebalanceResult(summary=summary, moves=moves)


def get_operational_status() -> str:
    with get_connection() as conn:
        bases = conn.execute(
            'SELECT id, name, priority, min_staff, required_vehicle FROM bases ORDER BY priority ASC, name ASC'
        ).fetchall()
        lines = ['📍 Estado operativo actual']
        for base in bases:
            staff = conn.execute(
                '''
                SELECT p.full_name, p.role, v.code AS vehicle_code, v.vehicle_type
                FROM assignments a
                JOIN personnel p ON p.id = a.person_id
                LEFT JOIN vehicles v ON v.id = a.vehicle_id
                WHERE a.base_id = ? AND a.active = 1
                ORDER BY CASE p.role WHEN 'medico' THEN 0 WHEN 'enfermero' THEN 1 ELSE 2 END, p.full_name ASC
                ''',
                (base['id'],),
            ).fetchall()
            absent = conn.execute(
                '''
                SELECT COUNT(*) AS total
                FROM personnel
                WHERE home_base_id = ? AND status = 'absent'
                ''',
                (base['id'],),
            ).fetchone()['total']
            vehicle_text = 'Sin vehículo asignado'
            if staff and staff[0]['vehicle_code']:
                vehicle_text = f"{staff[0]['vehicle_code']} ({staff[0]['vehicle_type']})"
            lines.append(
                f"\n• {base['name']} | prioridad {base['priority']} | mínimo {base['min_staff']} | vehículo {vehicle_text}"
            )
            if staff:
                for person in staff:
                    lines.append(f"   - {person['full_name']} ({person['role']})")
            else:
                lines.append('   - Sin personal asignado')
            lines.append(f"   - Ausencias en la base: {absent}")
        return '\n'.join(lines)


def get_people_list() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            'SELECT full_name FROM personnel ORDER BY full_name ASC'
        ).fetchall()
    return [row['full_name'] for row in rows]


def reset_demo_data() -> str:
    with get_connection() as conn:
        conn.execute("UPDATE personnel SET status = 'available'")
        conn.execute('DELETE FROM assignments')
        conn.execute('DELETE FROM absences')
        conn.execute('DELETE FROM alerts')
    result = rebalance_staff()
    return f'Demo reiniciada. {result.summary}'
