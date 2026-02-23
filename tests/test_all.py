from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

from faker import Faker

fake = Faker(['fr_FR']) # Pour avoir des noms et adresses qui ressemblent à la réalité

def test_creation_massive_clients():
    for _ in range(10):
        payload = {
            "nom_client": fake.company(),
            "code_client": fake.unique.bothify(text='CLIENT-####'),
            "matricule_fiscal": fake.bothify(text='#######?'),
            "adresse": fake.address(),
            "statut": "Resident",
            "email": fake.unique.email(),
            "telephone": fake.phone_number()
        }
        response = client.post("/clients/", json=payload)
        assert response.status_code == 201
        
