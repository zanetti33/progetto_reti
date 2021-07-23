# -*- coding: utf-8 -*-
"""
Created on Mon Jul  5 12:28:12 2021

@author: loren
"""
import random
import numpy as np
import tkinter as tk
import socket
from time import sleep
import threading

TOT_QUESTIONS = 15
TIME_START = 3
TIME_GAME = 40
questions_made = 0
score = 0
game_finished = False
indexes = np.empty(TOT_QUESTIONS)

questions = {
    0: ["Passa attraverso il vetro senza romperlo", "Luce"],
    1: ["Il cerchio che lo rese famoso non lo possiamo ammirare, ci restano però numerosi suoi capolavori.", "Giotto"],
    2: ["Il numero che moltiplicato per 7 dà la metà di 42?", "3"],
    3: ["La regione più piccola in Italia", "Valle d'Aosta"],
    4: ["Il pianeta più lontano dal sole?", "Plutone"],
    5: ["Il numero di secondi in un giorno", "86400"],
    6: ["La seconda lingua più parlata al mondo", "Spagnolo"],
    7: ["Lo stato più popoloso al mondo", "Cina"],
    8: ["Lo stato più esteso al mondo", "Russia"],
    9: ["Gli anni che passano dal 29 Febbraio al successivo 29 Febbraio", "4"],
    10: ["Il numero di corde in un basso", "4"],
    11: ["Il numero di note musicali", "7"],
    12: ["Il numero di bit in 16 KB", "128000"],
    13: ["Il presidente della Repubblica", "Sergio Mattarella"],
    14: ["Che animale è Winnie the Pooh?", "Orso"]
}

          

#La funzione che segue gestisce l'invio dei messaggi.
def send(event=None):
    global sck_closed
    #leggo il messaggio dell'utente
    msg = entry_field.get()
    my_msg.set("")
    # invia il messaggio sul socket
    client.send(msg.encode("utf8"))
    #nel caso fosse {quit} chiudo la connesione
    if msg == "{quit}":
        client.close()
        sck_closed = True
    #nel caso fosse {play} faccio partire una partita
    elif msg == "{play}":
        threading._start_new_thread(start_game, ())

def count_down(my_timer, is_game_timer):
    global client, score
    #se finisce il tempo, il gioco si chiude prima per che finisca (per il trabocchetto) o se si perde la connessione finisce il count down
    while my_timer > 0 and not game_finished and not sck_closed:
        lbl_timer["text"] = my_timer
        sleep(1)
        my_timer -= 1
        
    #se il count down era per la partita e non per il conto alla rovescia, sono ancora collegato mando il risultato e la partita non è finita precocemente
    if is_game_timer and not game_finished:
        if not sck_closed:
            client.send(("{result}" + str(score)).encode("utf8"))
        #se non sono più collegato non mando il risultato ma chiudo comunque la finestra
        stop_game()
        
    
def stop_game():
    global game_finished
    #se finisce il gioco modifico la flag, disabilito tutte le parti della gui di gioco e la chiudo
    game_finished = True
    enable_disable_buttons("disable")
    enable_disable_textbox("disable")
    game_window.withdraw()
    
def ask_question():
    global index 
    #estraggo l'indice della prossima domanda e la mostro all'utente
    index = indexes[questions_made]
    question, aswer = questions.get(index)
    lbl_question2["text"] = question
    
def aswer_question():
    global index, score
    #leggo la risposta dell'utente
    guess = answer_field.get()
    answer_field.set("")
    question, correct_answer = questions.get(index)
    #se è giusta guadagna un punto
    if guess == correct_answer:
        score += 1
        lbl_result["text"] = "CORRECT!"
    #altrimenti ne perde uno
    else:
        score -= 1
        lbl_result["text"] = "WRONG!"
    #aggiorno il punteggio sulla gui e torno alle opzioni a, b, c
    lbl_score["text"] = str(score)
    enable_disable_buttons("enable")
    enable_disable_textbox("disable")
    
        
def enable_disable_buttons(todo):
    #abilita i bottoni a,b,c
    if todo == "disable":
        btn_a.config(state=tk.DISABLED)
        btn_b.config(state=tk.DISABLED)
        btn_c.config(state=tk.DISABLED)
    #o li disabilita
    else:
        btn_a.config(state=tk.NORMAL)
        btn_b.config(state=tk.NORMAL)
        btn_c.config(state=tk.NORMAL)
        
def enable_disable_textbox(todo):
    #abilita il text field e il bottone per inviare una risposta
    if todo == "disable":
        answer_send_button.config(state=tk.DISABLED)
        answer_entry_field.config(state=tk.DISABLED)
    #o li disabilita
    else:
        answer_send_button.config(state=tk.NORMAL)
        answer_entry_field.config(state=tk.NORMAL)        
        
def start_game():
    global questions_made, indexes, score, game_finished
    #inizializzo tutte le variabile per giocare
    game_finished = False
    indexes = np.arange(0, TOT_QUESTIONS)
    #compreso l'ordine casuale delle domande
    np.random.shuffle(indexes);
    questions_made = 0
    score = 0
    #apro la gui della partita e inizio il conto alla rovescia prima di iniziare
    game_window.deiconify()
    lbl_time_left["text"] = "   Game starts in:  "
    threading._start_new_thread(count_down, (TIME_START, False))
    lbl_result["text"] = ""
    lbl_score["text"] = str(score)
    sleep(TIME_START)
    #finito il conto alla rovescia parte il gioco vero e proprio
    enable_disable_buttons("enable")
    lbl_time_left["text"] = "      Time left:    "
    threading._start_new_thread(count_down, (TIME_GAME, True))


def choice():
    global questions_made
    #invece di scegliere a priori quale tasto tra a,b e c è un trabocchetto sorteggio sempre con una probabilità del 33%
    #che da parte dell'utente è esattamente come indovinare da 3 opzioni a caso quella sbagliata
    if random.randint(0,3) == 0:
        #se prende il trabocchetto lo comunico al server e fermo la partita
        lbl_question2["text"] = "TRICK!!"
        client.send("{trick}".encode("utf8"))
        stop_game()
        #e mando il risultato
        if not sck_closed:
            client.send(("{result}" + str(score)).encode("utf8"))
    elif questions_made == TOT_QUESTIONS:
        #se sono finite le domande vengono disabilitati i tasti ma il timer continua fino alla fine
        lbl_question2["text"] = "No more questions..."
        enable_disable_buttons("disable")
    else:
        #se non viene preso il trabocchetto si passa alla prossima domanda
        enable_disable_buttons("disable")
        enable_disable_textbox("enable")
        ask_question()
        questions_made += 1
        
      
def receive():
    while True:
        try:
            #quando viene chiamata la funzione receive, si mette in ascolto dei messaggi che
            #arrivano sul socket
            msg = client.recv(BUFSIZ)
            #visualizziamo l'elenco dei messaggi sullo schermo
            #e facciamo in modo che il cursore sia visibile al termine degli stessi
            msg_list.insert(tk.END, msg.decode("utf8"))
            # Nel caso di errore e' probabile che il client abbia abbandonato la chat.
        except OSError:  
            break
        
# FINESTRA DI CHAT PRINCIPALE
window_main = tk.Tk()
window_main.title("Chat Client")
#creiamo il Frame per contenere i messaggi
messages_frame = tk.Frame(window_main)
#creiamo una scrollbar per navigare tra i messaggi precedenti.
scrollbar = tk.Scrollbar(messages_frame)

my_msg = tk.StringVar()
my_msg.set("Write hear.")
# La parte seguente contiene i messaggi.
msg_list = tk.Listbox(messages_frame, height=30, width=100, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
msg_list.pack(side=tk.LEFT, fill=tk.BOTH)
msg_list.pack()
messages_frame.pack()

#Creiamo il campo di input e lo associamo alla variabile stringa
entry_field = tk.Entry(window_main, textvariable=my_msg)
# leghiamo la funzione send al tasto Return
entry_field.bind("<Return>", send)

entry_field.pack()
#creiamo il tasto invio e lo associamo alla funzione end
send_button = tk.Button(window_main, text="Send", command=send)
#integriamo il tasto nel pacchetto
send_button.pack()


#INTERFACCIA DEL GIOCO

game_window = tk.Toplevel()
game_window.title("Game Client")
    
    
top_frame = tk.Frame(game_window)
    
top_left_frame = tk.Frame(top_frame, highlightbackground="green", highlightcolor="green", highlightthickness=1)
lbl_your_score = tk.Label(top_left_frame, text="     Score:     ", foreground="blue", font = "Helvetica 14 bold")
lbl_score = tk.Label(top_left_frame, text=" ", font = "Helvetica 24 bold", foreground="blue")
lbl_your_score.grid(row=0, column=0, padx=5, pady=5)
lbl_score.grid(row=1, column=0, padx=5, pady=5)
top_left_frame.pack(side=tk.LEFT, padx=(10, 10))
    
    
top_right_frame = tk.Frame(top_frame, highlightbackground="green", highlightcolor="green", highlightthickness=1)
lbl_time_left = tk.Label(top_right_frame, text="     Time left:     ", foreground="blue", font = "Helvetica 14 bold")
lbl_timer = tk.Label(top_right_frame, text=" ", font = "Helvetica 24 bold", foreground="blue")
lbl_time_left.grid(row=0, column=0, padx=5, pady=5)
lbl_timer.grid(row=1, column=0, padx=5, pady=5)
top_right_frame.pack(side=tk.RIGHT, padx=(10, 10))
    
top_frame.pack_forget()
    
middle_frame = tk.Frame(game_window)
    
lbl_line = tk.Label(middle_frame, text="***********************************************************").pack()
lbl_line = tk.Label(middle_frame, text="**** GAME LOG ****", font = "Helvetica 13 bold", foreground="blue").pack()
lbl_line = tk.Label(middle_frame, text="***********************************************************").pack()
    
round_frame = tk.Frame(middle_frame)
lbl_desc = tk.Label(round_frame, text="Choose a letter and answer the question you get!")
lbl_desc.pack()
lbl_question = tk.Label(round_frame, text="Question: " + "None", font = "Helvetica 12 bold")
lbl_question.pack()
lbl_question2 = tk.Label(round_frame, text="" + "None", font = "Helvetica 12 bold")
lbl_question2.pack()
lbl_result = tk.Label(round_frame, text=" ", foreground="blue", font = "Helvetica 14 bold")
lbl_result.pack()
round_frame.pack(side=tk.TOP)
    
final_frame = tk.Frame(middle_frame)
lbl_line = tk.Label(final_frame, text="***********************************************************").pack()
lbl_final_result = tk.Label(final_frame, text=" ", font = "Helvetica 15 bold", foreground="blue")
lbl_final_result.pack()
lbl_line = tk.Label(final_frame, text="***********************************************************").pack()
final_frame.pack(side=tk.TOP)
    
middle_frame.pack_forget()
    
# creo un answer_frame in cui ci sarà il textbox per la risposta e il tasto per inviarla
answer_field = tk.StringVar()
answer_field.set("Write hear.")
answer_frame = tk.Frame(middle_frame)
lbl_answer = tk.Label(answer_frame, text = "Answer:")
lbl_answer.pack(side=tk.LEFT)
answer_entry_field = tk.Entry(answer_frame, textvariable = answer_field, state=tk.DISABLED)
answer_entry_field.pack(side=tk.LEFT)
answer_send_button = tk.Button(answer_frame, text="Send", command=lambda : aswer_question(), state=tk.DISABLED)
answer_send_button.pack(side=tk.LEFT)
answer_frame.pack(side=tk.TOP)
    
button_frame = tk.Frame(game_window)
btn_a = tk.Button(button_frame, text="A", command=lambda : choice(), state=tk.DISABLED)
btn_b = tk.Button(button_frame, text="B", command=lambda : choice(), state=tk.DISABLED)
btn_c = tk.Button(button_frame, text="C", command=lambda : choice(), state=tk.DISABLED)
btn_a.grid(row=0, column=0)
btn_b.grid(row=0, column=1)
btn_c.grid(row=0, column=2)
button_frame.pack(side=tk.BOTTOM)
    
lbl_question["text"] = "Question: "
lbl_final_result["text"] = "FINAL RESULT: "
lbl_your_score["text"] = "Score: "
top_frame.pack()
middle_frame.pack()
#----Connessione al Server----
HOST = input('Inserire il Server host: ')
PORT = input('Inserire la porta del server host: ')

sck_closed = False
BUFSIZ = 1024
ADDR = (HOST, int(PORT))

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

threading._start_new_thread(receive, ())
game_window.withdraw()
window_main.mainloop()