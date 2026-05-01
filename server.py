import socket
import threading
import json
import os
import time

HOST = '0.0.0.0'
PORT        = 5000  
MY_DOMAIN   = 'local.ro'
BUFFER_SIZE = 4096

KNOWN_DOMAINS = {
    'extern.ro': ('server_extern', 8888)
}

DIRECTOR_MAILBOXES = "mailboxes"
os.makedirs(DIRECTOR_MAILBOXES, exist_ok=True)

# Am modificat functia sa returneze o confirmare (True = livrat, False = eroare)
def forward_mesaj(domeniu, mesaj_dict):
    ip_dest, port_dest = KNOWN_DOMAINS[domeniu]
    s_forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s_forward.connect((ip_dest, port_dest))
        comanda = f"SEND {json.dumps(mesaj_dict)}"
        s_forward.sendall(comanda.encode('utf-8'))
        
        # Asteptam confirmarea si o ignoram (ne intereseaza doar ca n-a dat eroare conexiunea)
        s_forward.recv(BUFFER_SIZE)
        return True, "Livrat la serverul extern"
        
    except ConnectionRefusedError:
        return False, "Serverul destinatie este oprit/indisponibil"
    except Exception as e:
        return False, f"Eroare retea: {e}"
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
                    
                    # Aici vom colecta statusul pentru fiecare adresa
                    raport_livrare = {}
                    
                    for destinatar in destinatari:
                        if '@' not in destinatar:
                            raport_livrare[destinatar] = "Eroare: Adresa invalida"
                            continue 
                            
                        nume_user, domeniu_user = destinatar.split('@', 1)
                        
                        if domeniu_user == MY_DOMAIN:
                            folder_dest = os.path.join(DIRECTOR_MAILBOXES, destinatar)
                            os.makedirs(folder_dest, exist_ok=True)
                            cale_fisier = os.path.join(folder_dest, f"msg_{int(time.time() * 1000)}.json")
                            with open(cale_fisier, "w") as f:
                                json.dump(date_email, f, indent=4)
                            
                            # Adaugam in raport
                            raport_livrare[destinatar] = "OK (Salvat local)"
                            
                        elif domeniu_user in KNOWN_DOMAINS:
                            mesaj_rutat = date_email.copy()
                            mesaj_rutat["recipients"] = [destinatar]
                            
                            # Apelam functia si salvam rezultatul in raport
                            succes, motiv = forward_mesaj(domeniu_user, mesaj_rutat)
                            if succes:
                                raport_livrare[destinatar] = "OK (Rutat)"
                            else:
                                raport_livrare[destinatar] = f"EROARE ({motiv})"
                                
                        else:
                            # Domeniu necunoscut
                            raport_livrare[destinatar] = "EROARE (Domeniu necunoscut/neconfigurat)"
                    
                    # Convertim raportul inapoi in text JSON ca sa-l trimitem clientului
                    raspuns = json.dumps(raport_livrare)
                    
                except json.JSONDecodeError:
                    raspuns = "EROARE_JSON: Format invalid."

            elif comanda == 'DISCONNECT':
                raspuns = "Deconectat."
                conexiune.sendall(raspuns.encode('utf-8'))
                break

            conexiune.sendall(raspuns.encode('utf-8'))
            
    except Exception as e:
        pass
    finally:
        conexiune.close()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()

print(f"Server {MY_DOMAIN} pe {HOST}:{PORT}")
while True:
    try:
        conexiune, adresa_client = server_socket.accept()
        thread = threading.Thread(target=proceseaza_client, args=(conexiune, adresa_client))
        thread.start()
    except KeyboardInterrupt:
        break