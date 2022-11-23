##Progra## 
##  Copyright (C) 2021 Francesco Del Castillo - Comune di Rivoli
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU Affero General Public License as
##  published by the Free Software Foundation, either version 3 of the
##  License, or (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU Affero General Public License for more details.
##
##  You should have received a copy of the GNU Affero General Public License
##  along with this program.  If not, see <https://www.gnu.org/licenses/>. 

## Programma per inviare un lotto di messaggi IO con promemoria di scadenza della CI e istruzioni per prendere un appuntamento
## I dati per l'invio sono sono contenuti in un CSV (con delimitatore ;) con i seguenti dati (ordine e nome delle etichette non sono rilevanti e possono essere presenti ulteriori colonne):
## codice_fiscale: codice fiscale dell'intestatario del documento in scadenza
## dataScadenzaDocumento: nel formato gg/mm/AAAA (in realtà il campo viene passato come stringa)

## Il file CSV con i dati è passato come argomento da linea di comando
## Il programma guida attraverso i seguenti passaggi:
## 1. converte CSV in tabella di lavoro e crea un JSON con gli stessi dati (TIMESTAMP - Lotto)
## 2. controlla lo stato di sottoscrizione dei codici fiscali presenti nel CSV e crea tabella di alvoro e JSON con 4 liste: iscritti, non iscritti, senza IO, non verificabili. Crea un JSON con il riusltato dell'interrogazione (TIMESTAMP - RisultatoCF)
## 3. invia il messaggio IO ai codici fiscali iscritti e crea un JSON con gli esiti (TIMESTAMP - EsitoInvii)
## 4. crea un file di log TIMESTAMP - Lotto.log con le operazioni salienti (già mostrate a video durante l'esecuzione).
## Tutte le operazioni e le interazioni con le API di IO sono annotate nel log appIO.log
## Il log delle azioni del modulo requests (dialogo con web service remoto) sono annotate in apposito log nella cartella di lotto.

## Il testo del messaggio IO è definito in preparaDati.py

import preparaDati
import parlaConIO
import serviziIO
import csv
import sys
import time
import os.path
import os

###import per annotare il log di requests
import logging
from http.client import HTTPConnection  # py3
log = logging.getLogger('urllib3')
log.setLevel(logging.DEBUG)

listaOK = preparaDati.listaOK ##risposte da interpretare come sì come risposta affermativa in caso di domanda posta dal programma
crea = preparaDati.crea_body_scadenzaCI ##indicare qui la funzione per la creazione del body del messaggio
##corrispondenzeDiDefault = {} ## Questo dizioanrio DEVE essere sempre presente
corrispondenzeDiDefault = {'dataScadenzaDocumento': 'dataScadenzaDocumento', 'codiceFiscale': 'codiceFiscale'}
data_lotto = preparaDati.timestamp()

## Selezione del servizio IO da utilizzare (qui fisso)
servizioIO="SCI" ## codice del servizio IO come definito in serviziIO.py

## Inizializzazione di cartella di lotto, file di output e logging
path = preparaDati.crea_cartella(servizioIO, data_lotto) # crea la cartella di lavoro del lotto
lottoLog = path + data_lotto + "-" + "Lotto.log"
lottoJson = path + data_lotto + "-" + "Lotto.json"
erroriCSV = path + data_lotto + "-" + "ErroriCSV.csv"
risultatoCFJson = path + data_lotto + "-" + "RisultatoCF.json"
esitoInviiJson = path + data_lotto + "-" + "EsitoInvii.json"
inviiNonElaborati = path + data_lotto + "-" + "messaggiNonElaborati.csv" #NEW
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
      stampa("Per favore indicalo nel seguente modo: python inviaLottoScadenzaCI.py <nomeDelTuoFile.csv>")
      q = input("Premi INVIO/ENTER per terminare.")
      stampa("Programma terminato.")
      exit()
elif os.path.exists("scadenzaCI.csv"):
   usa_default = input("Non hai indicato il file con i dati da processare. \nHo trovato il file scadenzaCI.csv. Vuoi usare questo? (Sì/No): ")
   if usa_default in listaOK:
         stampa("OK, proseguo con questo file.")
         nomeFileDati = "scadenzaCI.csv"
   else:
         stampa("Per favore indica il file con i dati da processare nel seguente modo:")
         stampa("python inviaLottoScadenzaCI.py <nomeDelTuoFile.csv>")
         q = input("Premi INVIO/ENTER per terminare.")
         stampa("Programma terminato.")
         exit()
else:
   stampa("Non hai indicato il file CSV con i dati da processare. Per favore indicalo nel seguente modo:")
   stampa("python inviaLottoScadenzaCI.py <nomeDelTuoFile.csv>")
   q = input("Premi INVIO/ENTER per terminare.")
   stampa("Programma terminato.")
   exit()

#sezione per l'elaborazione del CSV con i dati da processare e creazione di tabella, JSON dei dati e csv con eventuali righe del csv originario con errori
(tabellaDati, tabellaErrori, righeErrori) = preparaDati.importa_da_csv(nomeFileDati)
if tabellaDati==[]:
    print("niente da elaborare, ciao.")
    q = input("Premi INVIO/ENTER per terminare.")
    stampa("Programma terminato.")
    exit()
else:
   etichetteCSV = list(tabellaDati[0].keys())
preparaDati.esporta_json(tabellaDati, lottoJson, data_lotto)
stampa("CSV elaborato. Il file JSON " + lottoJson +" contiene i dati estratti.")

if len(tabellaErrori) > 1:
   preparaDati.esporta_csv(tabellaErrori, erroriCSV, data_lotto)
   stampa("ATTENZIONE: il CSV contiene almeno una riga con errori. Ho ignorato queste righe e le ho raccolte nel file " + erroriCSV + ".")
   stampa("Le righe del CSV con errori sono le seguenti: " + str(righeErrori))
   q = input("Premi INVIO/ENTER per proseguire")

## SEZIONE per definire le corrispondenze fra argomenti della funzione di creazione del body e il CSV con i dati
argomenti = preparaDati.recuperaArgomenti(crea)
argomentiDiDefault = list(corrispondenzeDiDefault.keys())
etichetteDiDefault = list(corrispondenzeDiDefault.values())
if (argomentiDiDefault == argomenti and set(etichetteDiDefault) <= set(etichetteCSV)) == False:
   stampa("Corrispondenze argomenti-CSV assenti o non valide.")
   corrispondenze = preparaDati.mappa(argomenti,etichetteCSV)
else:
   stampa("------------")
   stampa("Ho individuato le seguenti corrispondenze:")
   stampa(str(corrispondenzeDiDefault))
   stampa("------------")
   e = input("Confermi le corrispondenze (Sì/No)? ")
   if e in listaOK:
      stampa("Corrispondenze confermate.")
      corrispondenze = corrispondenzeDiDefault
   else:
      stampa("Hai scelto di modificare le corrispondenze.")
      corrispondenze = preparaDati.mappa(argomenti,etichetteCSV)
rigaDiEsempio = tabellaDati[0]
parametriDiEsempio = {}
for i in argomenti:
   parametriDiEsempio[i]=rigaDiEsempio[corrispondenze[i]]
stampa("------------")
stampa("In base alle tue indicazioni, ho individuato le corrispondenze come nel seguente esempio:")
stampa(str(parametriDiEsempio))
stampa("------------")
payloadDiEsempio = crea(**parametriDiEsempio)
stampa("In base alle tue indicazioni, il messaggio risulta formato come segue:")
stampa(str(payloadDiEsempio))
stampa("------------")
approva = input("Confermi le tue scelte (Sì/No)? ")
if approva not in listaOK:
   stampa("Messaggio di esempio non conforme alle aspettative. Ripeti la procedura.")
   q = input("Premi INVIO/ENTER per terminare.")
   stampa("Programma terminato.")
   exit()
else:
   stampa("Messaggio di esempio approvato.")

## Sezione per controllo dell'iscrizione dei CF al servizio IO
prosegui = ''
prosegui = input("Proseguo con il controllo dell'iscrizione degli utenti al servizio "+serviziIO.serviziIO[servizioIO]["nome"]+"? (Sì/No): ")
if prosegui in listaOK:
   stampa("Hai scelto di proseguire con la verifica delle iscrizioni.")
   print("Controllo lo stato di iscrizione al servizio.")
else:
   r = input("Premi INVIO/ENTER per terminare.")
   stampa("Programma terminato.")
   exit()

dizionarioCodiciFiscaliUtenti={} #serve per eliminare i codici fiscali presenti più volte

for riga in tabellaDati:
    cf = riga[corrispondenze["codiceFiscale"]]
    if cf:
       dizionarioCodiciFiscaliUtenti[cf]=""
   
listaCodiciFiscaliUtenti = list(dizionarioCodiciFiscaliUtenti.keys())

(risultato, codaNonElaborata) = parlaConIO.controllaCF(listaCodiciFiscaliUtenti, servizioIO)  ##NEW

stampa("------------")
stampa("Codici fiscali elaborati = "+str(len(listaCodiciFiscaliUtenti)))
stampa("Utenti con app IO iscritti = "+str(len(risultato["iscritti"])))
stampa("Utenti con app IO non iscritti = "+str(len(risultato["nonIscritti"])))
stampa("Utenti senza app IO = "+str(len(risultato["senzaAppIO"])))
stampa("Errori di interrogazione = "+str(len(risultato["inErrore"])))
stampa("Trovi il risultato dell'interrogazione delle iscrizioni al servizio nel file JSON " + risultatoCFJson + ".")
stampa("------------")

preparaDati.esporta_json(risultato, risultatoCFJson, data_lotto)

if codaNonElaborata:  ##NEW
   stampa("ATTENZIONE: l'interrogazione si è interrotta per sovraccarico del server IO.")
   stampa("Non è possibile proseguire. Riprova più tardi.")
   preparaDati.termina()

## Invio dei messaggi
prosegui = ''
prosegui = input("Vuoi proseguire con l'invio verso gli utenti iscritti al servizio IO "+serviziIO.serviziIO[servizioIO]["nome"]+"? (Sì/No):")
if prosegui in listaOK:
   stampa("Proseguo con l'invio.")
   stampa("In attesa di migliorare questo programma, se qualcosa andrà storto nella comunicazione con IO interroga i file di log e i file JSON prodotti.")
   stampa("Trovi tutti questi file nella cartella di lavoro del lotto: " + path +".")
else:
   q = input("Premi INVIO/ENTER per terminare.")
   stampa("Programma terminato.")
   exit()

invii = []

# togliere il commento da queste righe se si vuole fare un test offline
# risultato["iscritti"].append("AAAAAA00A00A000A")
# risultato["iscritti"].append("AAA")


if len(risultato["iscritti"]) == 0:
    stampa("Nessun messaggio da inviare, ciao.")
    invii = ["Nessun messaggio inviato."] #migliorare, perche' cosi' ho un json non omogeneo con gli altri
    preparaDati.esporta_json(invii, esitoInviiJson, data_lotto)
    preparaDati.termina()
else:
    t = 0 #pausa iniziale fra due iterazioni
    tmax = 0.2 #limite massimo della pausa fra due iterazioni raggiunto il quale si abbandona l'interrogazione
    passo = 0.1 #incremento della pausa fra due iterazioni a ogni errore
    pausa = 3 #pausa una tantum in seguito a errore per server sovraccarico
    datiInCoda = [] #lista vuoto per raccogliere la coda di tabellaDati eventualmente non elaborata
    for riga in tabellaDati:
        inviato = False
        while not inviato:
           if t >= tmax:
                stampa("Il sistema è sovraccarico, interrompo l'invio dei messaggi.")
                datiInCoda = tabellaDati[tabellaDati.index(riga):]
                stampa("Nella cartella di lotto trovi il file " + inviiNonElaborati + " da usare per completare l'invio.")
                messaggiInCoda=[]
                messaggiInCoda.append(etichetteCSV)
                for i in datiInCoda:
                   messaggioInCoda = i.values()
                   messaggiInCoda.append(messaggioInCoda)
                preparaDati.esporta_csv(messaggiInCoda, inviiNonElaborati, data_lotto)
                if invii:
                   stampa("Invio del lotto di messaggi interrotto prima del termine.")
                   stampa("Invii tentati: " + str(len(invii)) + ".")
                   a = sum([1 for i in invii if i["status_code"] == 201])
                   stampa("Invii accettati: " + str(a) + ".")
                   stampa("Consulta il file JSON " + esitoInviiJson + " per i dettagli dei singoli invii.")
                   preparaDati.esporta_json(invii, esitoInviiJson, data_lotto)
                else:
                   stampa("Nessun messaggio inviato.")
                   invii = ["Nessun messaggio inviato."] #migliorare, perche' cosi' ho un json non omogeneo con gli altri
                   preparaDati.esporta_json(invii, esitoInviiJson, data_lotto)
                preparaDati.termina()
           else:
              if riga[corrispondenze["codiceFiscale"]] in risultato["iscritti"]:
                  time.sleep(t)
                  parametri = {}
                  for i in argomenti:
                     parametri[i] = riga[corrispondenze[i]]
                  payload = crea(**parametri)
                  timestamp_submit=preparaDati.timestamp()
                  messaggio = parlaConIO.submitMessage(riga[corrispondenze["codiceFiscale"]], servizioIO, payload)
                  print(payload)
                  # print(messaggio)
                  invio={}
                  invio["timestamp"]=str(timestamp_submit)
                  invio["dataLotto"]=data_lotto
                  invio["servizioIO"]=servizioIO
                  invio["codiceFiscale"]=riga[corrispondenze["codiceFiscale"]]
                  invio["testo"]=payload
                  invio["status_code"]=messaggio.status_code
                  if messaggio.status_code == 201:
                     invio["esito"] = "Accettato"
                     invio["id"] = messaggio.json()["id"]
                     invii.append(invio)
                     inviato = True
                  elif messaggio.status_code == 429:  ## 429 è lo status code del sovraccarico del server IO
                     print("Il server IO è sovraccarico, attendo e inserisco una pausa fra le prossime richieste.")
                     t += passo
                     time.sleep(pausa)
                  else:
                     invio["esito"] = "Non accettato"
                     invio["motivo"] = messaggio.json()["title"]
                     invii.append(invio)
                     inviato = True
              else:
                  print("utente non iscritto")
                  inviato = True
    
stampa("Invio del lotto di messaggi terminato.")
stampa("Invii tentati: " + str(len(invii)) + ".")
a = sum([1 for i in invii if i["status_code"] == 201])
stampa("Invii accettati: " + str(a) + ".")
stampa("Consulta il file JSON " + esitoInviiJson + " per i dettagli dei singoli invii.")

if invii: ##NEW
   preparaDati.esporta_json(invii, esitoInviiJson, data_lotto)
   
q = input("Premi INVIO/ENTER per terminare")
exit()
