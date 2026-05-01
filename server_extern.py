import socket
import threading
import json
import os
import time

# --- CONFIGURAREA SERVERULUI ---
# Aici definim cine suntem si ce alte servere cunoastem
HOST = '0.0.0.0'
PORT        = 8888
MY_DOMAIN   = 'extern.ro'
BUFFER_SIZE = 4096

# Agenda noastra (Mapping domeniu -> IP, Port)
KNOWN_DOMAINS = {}

DIRECTOR_MAILBOXES = "mailboxes_extern"
os.makedirs(DIRECTOR_MAILBOXES, exist_ok=True)

# Functie noua: Serverul actioneaza ca un client pentru a da mesajul mai departe
def forward_mesaj(domeniu, mesaj_dict):
    ip_dest, port_dest = KNOWN_DOMAINS[domeniu]
    
    print(f"[RUTARE] Incerc trimiterea catre {domeniu} ({ip_dest}:{port_dest})...")
    s_forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s_forward.connect((ip_dest, port_dest))
        
        # Impachetam mesajul la loc si il trimitem celuilalt server
        comanda = f"SEND {json.dumps(mesaj_dict)}"
        s_forward.sendall(comanda.encode('utf-8'))
        
        # Asteptam confirmarea de la celalalt server
        raspuns = s_forward.recv(BUFFER_SIZE).decode('utf-8')
        print(f"[RUTARE SUCCES] Raspuns de la {domeniu}: {raspuns}")
        
    except ConnectionRefusedError:
        print(f"[RUTARE EROARE] Serverul pentru {domeniu} este indisponibil (picat)!")
    except Exception as e:
        print(f"[RUTARE EROARE] {e}")
    finally:
        s_forward.close()


def proceseaza_client(conexiune, adresa_client):
    try:
        while True:
            date_brute = conexiune.recv(BUFFER_SIZE)
            if not date_brute: break 
            
            mesaj_primit = date_brute.decode('utf-8').strip()
            parti = mesaj_primit.split(' ', 1)
            comanda = parti[0].upper()
            argumente = parti[1] if len(parti) > 1 else ''

            if comanda == 'SEND':
                try:
                    date_email = json.loads(argumente)
                    destinatari = date_email.get("recipients", [])
                    
                    # LOGICA NOUA DE RUTARE
                    for destinatar in destinatari:
                        # Separam "nume@domeniu.ro" -> nume = "nume", domeniu = "domeniu.ro"
                        if '@' not in destinatar:
                            continue # Ignoram adresele invalide
                            
                        nume_user, domeniu_user = destinatar.split('@', 1)
                        
                        if domeniu_user == MY_DOMAIN:
                            # E pentru noi! Salvam local (Pasul 3)
                            folder_dest = os.path.join(DIRECTOR_MAILBOXES, destinatar)
                            os.makedirs(folder_dest, exist_ok=True)
                            cale_fisier = os.path.join(folder_dest, f"msg_{int(time.time() * 1000)}.json")
                            with open(cale_fisier, "w") as f:
                                json.dump(date_email, f, indent=4)
                            print(f"[LIVRARE LOCALA] Salvat pt: {destinatar}")
                            
                        elif domeniu_user in KNOWN_DOMAINS:
                            # E pentru un server cunoscut! Il trimitem mai departe
                            # Creăm un mesaj nou doar cu destinatarul curent, pentru a nu trimite toată lista
                            mesaj_rutat = date_email.copy()
                            mesaj_rutat["recipients"] = [destinatar]
                            forward_mesaj(domeniu_user, mesaj_rutat)
                            
                        else:
                            # E un domeniu necunoscut
                            print(f"[EROARE DOMENIU] Nu stiu cum sa livrez la domeniul: {domeniu_user}")
                    
                    raspuns = "OK: Procesare destinatari finalizata."
                    
                except json.JSONDecodeError:
                    raspuns = "EROARE: JSON invalid."

            elif comanda == 'DISCONNECT':
                conexiune.sendall("OK: Deconectat.".encode('utf-8'))
                break

            conexiune.sendall(raspuns.encode('utf-8'))
            
    except Exception as e:
        pass
    finally:
        conexiune.close()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()

print("=" * 50)
print(f"  SERVER TCP pornit pe {HOST}:{PORT}")
print(f"  Domeniu gestionat: {MY_DOMAIN}")
print("=" * 50)

while True:
    try:
        conexiune, adresa_client = server_socket.accept()
        thread = threading.Thread(target=proceseaza_client, args=(conexiune, adresa_client))
        thread.start()
    except KeyboardInterrupt:
        break

server_socket.close()