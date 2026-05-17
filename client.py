import socket
import json

HOST        = '127.0.0.1'
PORT        = 5000
BUFFER_SIZE = 4096

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect((HOST, PORT))
    print("=" * 50)
    print(f"  Conectat la serverul {HOST}:{PORT}")
    print("  Comenzi: SEND, DISCONNECT")
    print("=" * 50)

    while True:
        comanda_utilizator = input("\n>> Introduceți comanda: ").strip()
        if not comanda_utilizator:
            continue
            
        comanda_upper = comanda_utilizator.upper()

        if comanda_upper == 'SEND':
            expeditor = input("  De la (ex. ion@local.ro): ").strip()
            destinatari_raw = input("  Catre (separati prin virgula, ex. ana@local.ro): ").strip()
            subiect = input("  Subiect: ").strip()
            continut = input("  Mesaj: ").strip()

            lista_destinatari = [d.strip() for d in destinatari_raw.split(",") if d.strip()]

            mesaj_dict = {
                "sender": expeditor,
                "recipients": lista_destinatari,
                "subject": subiect,
                "content": continut
            }

            argumente = json.dumps(mesaj_dict)
            
            comanda_finala = f"SEND {argumente}"
            client_socket.sendall(comanda_finala.encode('utf-8'))

        elif comanda_upper == 'DISCONNECT':
            client_socket.sendall(comanda_utilizator.encode('utf-8'))
            break
        else:
            client_socket.sendall(comanda_utilizator.encode('utf-8'))
        
        raspuns_brut = client_socket.recv(BUFFER_SIZE)
        raspuns_text = raspuns_brut.decode('utf-8')
        
        try:
            raport = json.loads(raspuns_text)
            print("\n[RAPORT DE LIVRARE]")
            for adresa, status in raport.items():
                print(f" -> {adresa}: {status}")
            print("-" * 30)
        except json.JSONDecodeError:
            print(f"[SERVER]: {raspuns_text}")

except Exception as e:
    print(f"[EROARE] {e}")
finally:
    client_socket.close()
    print("[CLIENT] Deconectat.")