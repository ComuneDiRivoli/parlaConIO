## Programma per inviare un lotto di messaggi IO con un messaggio di teto fisso, senza personalizzazioni.
## Il testo del messaggio è contenuto nella variaible "testoFisso", il titolo (oggetto) del messaggio nella varibiale "titolo".
## L'elenco dei codici fiscali a cui inviare è contenuto in un csv (nome di default listaCF) con i codici fiscali in una colonna che verrà chiesto di individuare.
## Il programma guida attraverso i seguenti passaggi:
## 1. converte CSV in tabella di lavoro e crea un JSON con gli stessi dati (TIMESTAMP - Lotto)
## 2. controlla lo stato di sottoscrizione dei codici fiscali presenti nel CSV e crea tabella di alvoro e JSON con 4 liste: iscritti, non iscritti, senza IO, non verificabili. Crea un JSON con il riusltato dell'interrogazione (TIMESTAMP - RisultatoCF)
## 3. invia il messaggio IO ai codici fiscali iscritti e crea un JSON con gli esiti (TIMESTAMP - EsitoInvii)
## 4. crea un file di log TIMESTAMP - Lotto.log con le operazioni salienti (già mostrate a video durante l'esecuzione).
## Tutte le operazioni e le interazioni con le API di IO sono annotate nel log appIO.log
## Il log delle azioni del modulo requests (dialogo con web service remoto) sono annotate in apposito log nella cartella di lotto.

## Il testo del messaggio IO è definito nella variabile "testoFisso"

import preparaDati
import parlaConIO
import serviziIO
import csv
import sys
import os.path
import os


###import per annotare il log di requests
import logging
from http.client import HTTPConnection  # py3
log = logging.getLogger('urllib3')
log.setLevel(logging.DEBUG)

listaOK = preparaDati.listaOK ##risposte da interpretare come sì come risposta affermativa in caso di domanda posta dal programma
data_lotto = preparaDati.timestamp()

testoFisso = "Per semplificare il rapporto con i suoi cittadini, il Comune distribuisce gratuitamente una casella di posta elettronica certificata (PEC). \n \n [Prenota un appuntamento] (https://prenota.comune.rivoli.to.it/pec-gratuita-per-i-cittadini-rivolesi) in Comune per ottenere la tua. \n \n Ulteriori dettagli [sul sito web del Comune] (https://secure.comune.rivoli.to.it/jportal/sprweb/JPModulo.do?MVPG=SprProcedimentoVis&id=746&rv=0&idc=7)."
titolo = "Richiedi la tua casella PEC gratuita"

##propone lista di servizi io e annota la scelta
print("Questi sono i servizi IO attualmente configurati per invio di testi fissi:")
for chiave in serviziIO.elencoServiziIOTestoFisso:
   print(chiave, ":", serviziIO.serviziIO[chiave]["nome"])
servizio = input("Quale servizio IO vuoi utilizzare? Indica il codice fra quelli elencati sopra: ")
if servizio in serviziIO.elencoServiziIOTestoFisso:
   servizioIO=servizio
else:
   servizio = input("Servizio non valido, ritenta. Indica il codice fra quelli elencati sopra: ")
   if servizio in serviziIO.elencoServiziIO:
      servizioIO = servizio
   else:
      print("Servizio indicato non valido.")
      q = input("Premi INVIO/ENTER per terminare l'esecuzione del programma.")
      print("Programma terminato.")
      exit()
      
## Inizializzazione di cartella di lotto, file di output e logging
path = preparaDati.crea_cartella(servizioIO, data_lotto) # crea la cartella di lavoro del lotto
lottoLog = path + data_lotto + "-" + "Lotto.log"
lottoJson = path + data_lotto + "-" + "Lotto.json"
risultatoCFJson = path + data_lotto + "-" + "RisultatoCF.json"
esitoInviiJson = path + data_lotto + "-" + "EsitoInvii.json"
requestsLog = path + data_lotto + "-" + "Requests.log"
fh = logging.FileHandler(requestsLog)
log.addHandler(fh)

# definisco la funzione stampa da usare al posto di print per scrivere il messaggio anche sul file Lotto.log - POI studaire un sistema migliore!!
def stampa(stringa):
   print(stringa)
   with open(lottoLog, 'a+') as fileLog:
      rigaDiLog = [preparaDati.timestamp(),stringa]
      fileLog.write(";".join(rigaDiLog))
      fileLog.write("\n")
      fileLog.flush()

stampa("Ciao " + os.getlogin() + "!") #apre il lotto di log salutando l'utente

# il programma attende di avere come argomento il nome del file CSV con i dati da processare. Se indicato ne verifica l'esistenza; se non indicato alcun file cerca il file con nome di default per il tipo di servizio IO
if len(sys.argv) > 1:
   if os.path.exists(sys.argv[1]):
      stampa("File "+sys.argv[1]+" trovato.")
      proseguire = input("Proseguire? (Sì/No):")
      if proseguire in listaOK:
         stampa("OK, proseguo.")
         nomeFileDati = sys.argv[1]
      else:
          q = input("Premi INVIO/ENTER per terminare.")
          stampa("Programma terminato.")
          exit()
   else:
      stampa("File di input non valido.")
      stampa("Per favore indicalo nel seguente modo: python inviaLottoNotizie.py <nomeDelTuoFile.csv>")
      q = input("Premi INVIO/ENTER per terminare.")
      stampa("Programma terminato.")
      exit()
elif os.path.exists("listaCF.csv"):
   usa_default = input("Non hai indicato il file con i dati da processare. \nHo trovato il file listaCF.csv. Vuoi usare questo? (Sì/No): ")
   if usa_default in listaOK:
         stampa("OK, proseguo con questo file.")
         nomeFileDati = "listaCF.csv"
   else:
         stampa("Per favore indica il file con i dati da processare nel seguente modo:")
         stampa("python inviaLottoNotizie.py <nomeDelTuoFile.csv>")
         q = input("Premi INVIO/ENTER per terminare.")
         stampa("Programma terminato.")
         exit()
else:
   stampa("Non hai indicato il file CSV con i dati da processare. Per favore indicalo nel seguente modo:")
   stampa("python inviaLottoNotizie.py <nomeDelTuoFile.csv>")
   q = input("Premi INVIO/ENTER per terminare.")
   stampa("Programma terminato.")
   exit()

#sezione per l'elaborazione del CSV con i dati da processare e creazione di tabella e JSON
tabellaDati = preparaDati.importa_da_csv(nomeFileDati)
if tabellaDati==[]:
    print("niente da elaborare, ciao.")
    q = input("Premi INVIO/ENTER per terminare.")
    stampa("Programma terminato.")
    exit()
else:
   chiaviCSV = list(tabellaDati[0].keys())
print("Il CSV importato ha le seguenti chiavi:")
for i in chiaviCSV:
   print(i)
chiaveCF = input("Indicare la chiave che contiene il codice fiscale: ")
while not chiaveCF in chiaviCSV:
   chiaveCF = input("Indicare la chiave che contiene il codice fiscale: ")

preparaDati.esporta_json(tabellaDati, lottoJson, data_lotto)

stampa("CSV elaborato. Il file JSON " + lottoJson +" contiene i dati estratti.")

#sezione per controllo testo fisso da inviare
stampa("In base alle configurazioni attuali sarà inviato il seguente messaggio:")
stampa("TITOLO: " + titolo)
stampa("TESTO: " + testoFisso)
approva = input("Confermi il messaggio (Sì/No)? ")
if approva not in listaOK:
   stampa("Messaggio  non conforme alle aspettative. Ripeti la procedura.")
   q = input("Premi INVIO/ENTER per terminare.")
   stampa("Programma terminato.")
   exit()
else:
   stampa("Messaggio approvato.")

#sezione per il controllo dell'iscrizione al servizio IO a partire dai codici fiscali presenti nel file CSV con i dati da elaborare
prosegui = ''
prosegui = input("Proseguo con il controllo dell'iscrizione degli utenti al servizio " + serviziIO.serviziIO[servizioIO]["nome"] + "? (Sì/No): ")
if prosegui in listaOK:
   stampa("Hai scelto di proseguire con la verifica delle iscrizioni.")
   print("Controllo lo stato di iscrizione al servizio.")
else:
   r = input("Premi INVIO/ENTER per terminare.")
   stampa("Programma terminato.")
   exit()

dizionarioCodiciFiscaliUtenti={} #serve per eliminare i codici fiscali presenti più volte

for riga in tabellaDati:
    cf = riga[chiaveCF]
    dizionarioCodiciFiscaliUtenti[cf]=""

listaCodiciFiscaliUtenti = list(dizionarioCodiciFiscaliUtenti.keys())

risultato = parlaConIO.controllaCF(listaCodiciFiscaliUtenti, servizioIO)
    
stampa("Codici fiscali elaborati = "+str(len(listaCodiciFiscaliUtenti)))
stampa("Utenti con app IO iscritti = "+str(len(risultato["iscritti"])))
stampa("Utenti con app IO non iscritti = "+str(len(risultato["nonIscritti"])))
stampa("Utenti senza app IO = "+str(len(risultato["senzaAppIO"])))
stampa("Errori di interrogazione = "+str(len(risultato["inErrore"])))
stampa("Trovi il risultato dell'interrogazione delle iscrizioni al servizio nel file JSON " + risultatoCFJson + ".")

preparaDati.esporta_json(risultato, risultatoCFJson, data_lotto)

## Invio dei messaggi
prosegui = ''
prosegui = input("Vuoi proseguire con l'invio verso gli utenti iscritti al servizio IO " + serviziIO.serviziIO[servizioIO]["nome"] + "? (Sì/No):")
if prosegui in listaOK:
   stampa("Proseguo con l'invio.")
   stampa("In attesa di migliorare questo programma, se qualcosa andrà storto nella comunicazione con IO interroga i file di log e i file JSON prodotti.")
   stampa("Trovi tutti questi file nella cartella di lavoro del lotto: " + path +".")
else:
   q = input("Premi INVIO/ENTER per terminare.")
   stampa("Programma terminato.")
   exit()

invii = []
if len(risultato["iscritti"]) == 0:
    stampa("Nessun messaggio da inviare, ciao.")
    invii = ["Nessun messaggio inviato."] #migliorare, perche' cosi' ho un json non omogeneo con gli altri
else:
    for riga in tabellaDati:
        if riga[chiaveCF] in risultato["iscritti"]:
            payload = preparaDati.crea_body_testoFisso(titolo, testoFisso, riga[chiaveCF])
            timestamp_submit=preparaDati.timestamp()
            messaggio = parlaConIO.submitMessage(riga[chiaveCF], servizioIO, payload)
            print(payload)
            print(messaggio)
            invio={}
            invio["timestamp"]=str(timestamp_submit)
            invio["dataLotto"]=data_lotto
            invio["servizioIO"]=servizioIO
            invio["codiceFiscale"]=riga[chiaveCF]
            invio["testo"]=payload
            invio["status_code"]=messaggio.status_code
            if messaggio.status_code == 201:
               invio["esito"] = "Accettato"
               invio["id"] = messaggio.json()["id"]
            else:
               invio["esito"] = "Non accettato"
               invio["motivo"] = messaggio.json()["title"]
            invii.append(invio)
        else:
            print(riga[chiaveCF],"- utente non iscritto")

preparaDati.esporta_json(invii, esitoInviiJson, data_lotto)
    
stampa("Invio del lotto di messaggi terminato.")
stampa("Invii tentati: " + str(len(invii)) + ".")
a = sum([1 for i in invii if i["status_code"] == 201])
stampa("Invii accettati: " + str(a) + ".")
stampa("Consulta il file JSON " + esitoInviiJson + " per i dettagli dei singoli invii.")

q = input("Premi INVIO/ENTER per terminare")
exit()
