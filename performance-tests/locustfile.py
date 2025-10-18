import random
import json
from locust import HttpUser, task, between


class PetClinicUser(HttpUser):
    wait_time = between(1, 3)  # Espera entre 1 a 3 segundos entre requisições
    
    def on_start(self):
        """Executado quando cada usuário inicia"""
        # Lista de IDs de proprietários conhecidos (1-10 existem por padrão)
        self.owner_ids = list(range(1, 11))
    
    @task(40)  # 40% das requisições
    def get_owners(self):
        """GET /api/customer/owners - Lista todos os proprietários"""
        with self.client.get("/api/customer/owners", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Falha ao obter lista de proprietários: {response.status_code}")
    
    @task(30)  # 30% das requisições
    def get_owner_by_id(self):
        """GET /api/customer/owners/{id} - Obtém proprietário específico"""
        owner_id = random.choice(self.owner_ids)
        with self.client.get(f"/api/customer/owners/{owner_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Falha ao obter proprietário {owner_id}: {response.status_code}")
    
    @task(20)  # 20% das requisições
    def get_vets(self):
        """GET /api/vet/vets - Lista todos os veterinários"""
        with self.client.get("/api/vet/vets", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Falha ao obter lista de veterinários: {response.status_code}")
    
    @task(10)  # 10% das requisições
    def create_owner(self):
        """POST /api/customer/owners - Cria novo proprietário"""
        # Gerar dados aleatórios para o novo proprietário
        random_num = random.randint(1000, 9999)
        owner_data = {
            "firstName": f"TestUser{random_num}",
            "lastName": f"Lastname{random_num}",
            "address": f"{random.randint(100, 999)} Test St",
            "city": f"TestCity{random.randint(1, 100)}",
            "telephone": f"{random.randint(1000000000, 9999999999)}"
        }
        
        headers = {'Content-Type': 'application/json'}
        
        with self.client.post("/api/customer/owners", 
                            data=json.dumps(owner_data), 
                            headers=headers, 
                            catch_response=True) as response:
            if response.status_code == 201:
                response.success()
                # Adicionar o novo ID à lista se retornado na resposta
                try:
                    new_owner = response.json()
                    if 'id' in new_owner:
                        self.owner_ids.append(new_owner['id'])
                except:
                    pass  # Ignorar erros de parsing JSON
            else:
                response.failure(f"Falha ao criar proprietário: {response.status_code}")