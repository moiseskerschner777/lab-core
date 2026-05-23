from datetime import date
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import SessionLocal
from models.patient import Patient
from models.practitioner import Practitioner


PATIENTS = [
    {
        "id": "11c5be47-3215-4890-a79f-9c2b2293a85e",
        "name_family": "Silva",
        "name_given": "Ana Paula",
        "birth_date": date(1988, 4, 12),
        "gender": "female",
        "active": True,
    },
    {
        "id": "e36e8749-a762-45ea-bd6b-63a5745d6e07",
        "name_family": "Oliveira",
        "name_given": "Carlos Eduardo",
        "birth_date": date(1979, 9, 3),
        "gender": "male",
        "active": True,
    },
    {
        "id": "664d2678-29ce-450e-ab50-bd463364ded6",
        "name_family": "Souza",
        "name_given": "Mariana",
        "birth_date": date(1995, 1, 27),
        "gender": "female",
        "active": True,
    },
    {
        "id": "57b22f32-fb64-4328-8aea-331c799e8c5b",
        "name_family": "Pereira",
        "name_given": "Joao Pedro",
        "birth_date": date(2001, 7, 18),
        "gender": "male",
        "active": True,
    },
    {
        "id": "cbf0c4f8-6414-4e62-a9d6-8f5fae25e87f",
        "name_family": "Costa",
        "name_given": "Fernanda",
        "birth_date": date(1983, 11, 22),
        "gender": "female",
        "active": True,
    },
    {
        "id": "62ad9f49-a889-4ca1-9ca0-bb0c3a2f5404",
        "name_family": "Rodrigues",
        "name_given": "Lucas",
        "birth_date": date(1992, 5, 8),
        "gender": "male",
        "active": True,
    },
    {
        "id": "21307f05-3ef0-4609-ad95-6ba417d6f5a0",
        "name_family": "Almeida",
        "name_given": "Beatriz",
        "birth_date": date(1974, 2, 14),
        "gender": "female",
        "active": True,
    },
    {
        "id": "10224d6f-5793-4118-872f-742af3d361ee",
        "name_family": "Lima",
        "name_given": "Rafael",
        "birth_date": date(1986, 12, 30),
        "gender": "male",
        "active": True,
    },
    {
        "id": "99ca7393-59ce-4db3-a795-a7c5b784698d",
        "name_family": "Gomes",
        "name_given": "Patricia",
        "birth_date": date(1998, 6, 5),
        "gender": "female",
        "active": True,
    },
    {
        "id": "17ae4441-d7dd-4f7c-bc55-7ca85bf4f677",
        "name_family": "Martins",
        "name_given": "Thiago",
        "birth_date": date(1969, 10, 9),
        "gender": "male",
        "active": True,
    },
]

PRACTITIONERS = [
    {
        "id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
        "name": "Dra. Helena Martins",
        "specialty": "Cardiologia",
        "council_type": "CRM",
        "council_number": "12345",
        "council_state": "SC",
        "active": True,
    },
    {
        "id": "8853e3c3-d0f9-469f-ae48-7813dc83b8ec",
        "name": "Dr. Ricardo Menezes",
        "specialty": "Clínica Geral",
        "council_type": "CRM",
        "council_number": "23456",
        "council_state": "SC",
        "active": True,
    },
    {
        "id": "35ca797f-5099-479d-91d5-fbe12a125b90",
        "name": "Dra. Camila Azevedo",
        "specialty": "Endocrinologia",
        "council_type": "CRM",
        "council_number": "34567",
        "council_state": "SC",
        "active": True,
    },
]


def insert_patient_if_missing(session, patient_data):
    if session.get(Patient, patient_data["id"]) is None:
        session.add(Patient(**patient_data))


def insert_practitioner_if_missing(session, practitioner_data):
    if session.get(Practitioner, practitioner_data["id"]) is None:
        session.add(Practitioner(**practitioner_data))


def main():
    session = SessionLocal()
    try:
        for patient_data in PATIENTS:
            insert_patient_if_missing(session, patient_data)
        for practitioner_data in PRACTITIONERS:
            insert_practitioner_if_missing(session, practitioner_data)
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    main()
