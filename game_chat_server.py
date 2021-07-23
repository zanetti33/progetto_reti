# Laboratorio di Programmazione di Reti - UniversitÃ  di Bologna - Campus di Cesena
# Giovanni Pau - Andrea Piroddi

#importiamo i moduli che utilizzeremo
import tkinter as tk
import socket
import threading
import random
import time


window = tk.Tk()
window.title("Server")

# Cornice superiore composta da due pulsanti (i.e. btnStart, btnStop)
topFrame = tk.Frame(window)
btnStart = tk.Button(topFrame, text="Start", command=lambda : start_server())
btnStart.pack(side=tk.LEFT)
btnStop = tk.Button(topFrame, text="Stop", command=lambda : stop_server(), state=tk.DISABLED)
btnStop.pack(side=tk.LEFT)
topFrame.pack(side=tk.TOP, pady=(5, 0))

# Cornice centrale composta da due etichette per la visualizzazione delle informazioni sull'host e sulla porta
middleFrame = tk.Frame(window)
lblHost = tk.Label(middleFrame, text = "Address: X.X.X.X")
lblHost.pack(side=tk.LEFT)
lblPort = tk.Label(middleFrame, text = "Port:XXXX")
lblPort.pack(side=tk.LEFT)
middleFrame.pack(side=tk.TOP, pady=(5, 0))

# Il frame client mostra l'area dove sono elencati i clients che partecipano al gioco
clientFrame = tk.Frame(window)
lblLine = tk.Label(clientFrame, text="**********Client List**********").pack()
scrollBar = tk.Scrollbar(clientFrame)
scrollBar.pack(side=tk.RIGHT, fill=tk.Y)
tkDisplay = tk.Text(clientFrame, height=10, width=30)
tkDisplay.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))
scrollBar.config(command=tkDisplay.yview)
tkDisplay.config(yscrollcommand=scrollBar.set, background="#F4F6F7", highlightbackground="grey", state="disabled")
clientFrame.pack(side=tk.BOTTOM, pady=(5, 10))


server = None
HOST_ADDR = '127.0.0.1'
HOST_PORT = 8080
BUFSIZ = 1024
maxResult = None
bestPlayer = ""
clients = []
clients_suffix = []
roles = ["the rogue", "the archer", "the mage", "the warrior", "the swordsman", "the paladin", "the priest"]

# Avvia la funzione server
def start_server():
    global server, HOST_ADDR, HOST_PORT, server_closed
    btnStart.config(state=tk.DISABLED)
    btnStop.config(state=tk.NORMAL)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print (socket.AF_INET)
    print (socket.SOCK_STREAM)
    
    server.bind((HOST_ADDR, HOST_PORT))
    server.listen(5)  # il server Ã¨ in ascolto per la connessione del client
    
    threading._start_new_thread(accept_clients, ())

    #inizializzo per estrarre i ruoli dei giocatori casualmente
    random.seed(time.time())
    
    lblHost["text"] = "Address: " + HOST_ADDR
    lblPort["text"] = "Port: " + str(HOST_PORT)
    
# Arresta la funzione server
def stop_server():
    global server, server_closed
    btnStart.config(state=tk.NORMAL)
    btnStop.config(state=tk.DISABLED)
    server.close()

def accept_clients():
    global server
    while True:
        try:
            # Nel caso di errore significa che abbiamo chiuso il server, quindi la funzione può semplicemente terminare
            client, addr = server.accept()
            clients.append(client)
            threading._start_new_thread(send_receive_client_message, (client, addr))
        except OSError:  
            break
        
# Funzione per ricevere messaggi dal client corrente E
# Invia quel messaggio agli altri client
def send_receive_client_message(client_connection, client_ip_addr):
    global server, clients, maxResult, bestPlayer

    client_connection.send("Write you name".encode("utf8"))
    
    # invia un messaggio di benvenuto al client e alla chat globale
    client_name = client_connection.recv(BUFSIZ).decode("utf8")
    
    #assegno un ruolo al giocatore appena entrato
    role_index = random.randint(0, len(roles) - 1)
    client_role = roles[role_index]
    
    #e creo il "suffisso" cioè il nome e il ruolo del client che appariranno quando il giocatore scrive un messaggio o gioca
    client_suffix = client_name + " " + client_role
    
    client_connection.send(("Welcome " + client_suffix + ", if you need help write {help}").encode("utf8"))
    broadcast(client_suffix + " joined the chat", "Master: ")
    
    
    clients_suffix.append(client_suffix)
    update_client_names_display(clients_suffix)  # aggiornare la visualizzazione dei nomi dei client
    
    #si mette in ascolto del thread del singolo client e ne gestisce l'invio dei messaggi o l'uscita dalla Chat
    while True:
        msg = client_connection.recv(BUFSIZ)
        if msg.startswith("{quit}".encode("utf8")):
            # trova l'indice del client, quindi lo rimuove da entrambi gli elenchi (elenco dei nomi dei client e elenco delle connessioni)
            idx = get_client_index(clients, client_connection)
            client_connection.close()
            del clients_suffix[idx]
            del clients[idx]
            update_client_names_display(clients_suffix)  # aggiorna la visualizzazione dei nomi dei client
            broadcast(client_suffix + " leaved the chat", "Master: ") #diciamo agli altri giocatori che quello corrente è uscito
            break
        elif msg.startswith("{play}".encode("utf8")):
            broadcast(client_suffix + " started a new adventure", "Master: ")
        elif msg.startswith("{help}".encode("utf8")):
            client_connection.send("{quit} to leave, {play} to start the game, {record} to view the record".encode("utf8"))
        elif msg.startswith("{record}".encode("utf8")):
            if maxResult == None:
                client_connection.send(("Nobody has played yet").encode("utf8"))
            else:
                client_connection.send(("The record is: " + str(maxResult) + " Detained by " + bestPlayer).encode("utf8"))
        elif msg.startswith("{result}".encode("utf8")):
            effmsg = msg.decode("utf8")
            result = int(effmsg.replace("{result}", ""))
            broadcast(client_suffix + " totalized " + str(result) + " points!", "Master: ")
            if maxResult == None or result > maxResult:
                maxResult = result
                bestPlayer = client_suffix
                broadcast(client_suffix + " beat the record!", " ")
        elif msg.startswith("{trick}".encode("utf8")):
            broadcast(client_suffix + " got TRICKED!!!", "Master: ")
        else: #se il client non usa un "comando speciale" significa che vuole mandare un messaggio agli altri client
            broadcast(msg.decode("utf8"), client_suffix + ": ")
            
    
    

# Aggiorna la visualizzazione del nome del client quando un nuovo client si connette O
# Quando un client connesso si disconnette
def update_client_names_display(name_list):
    tkDisplay.config(state=tk.NORMAL)
    tkDisplay.delete('1.0', tk.END)

    for c in name_list:
        tkDisplay.insert(tk.END, c+"\n")
    tkDisplay.config(state=tk.DISABLED)
    
# Restituisce l'indice del client corrente nell'elenco dei client
def get_client_index(client_list, curr_client):
    idx = 0
    for conn in client_list:
        if conn == curr_client:
            break
        idx = idx + 1

    return idx

# La funzione, che segue, invia un messaggio in broadcast a tutti i client.
def broadcast(msg, prefisso=""):
    for utente in clients:
        utente.send((prefisso + msg).encode("utf8"))
        
        
window.mainloop()