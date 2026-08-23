import requests

def test_aegis_connection():
    print("Iniciando prueba de conexión AEGIS -> Aletheia Core...")
    
    url = "http://localhost:8000/api/v1/execute"
    payload = {
        "client_id": "AEGIS",
        "task": "Dime un dato curioso corto y luego enciende mi Xbox",
        "session_context": {
            "xbox_network_ip": "192.168.1.55",
            "user_token": "simulated_token_123"
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        print("\n[Respuesta del Motor Aletheia]:")
        print(response.json())
    except requests.exceptions.ConnectionError:
        print("\n[Error]: Aletheia Core no está corriendo. Ejecuta 'python main.py' primero.")

if __name__ == "__main__":
    test_aegis_connection()
