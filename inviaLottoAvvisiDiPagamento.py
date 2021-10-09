## 
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

## Programma per inviare un lotto di messaggi IO con avviso di pagamento pagoPA
## I dati per l'invio sono sono contenuti in un CSV (con delimitatore ;) con i seguenti dati (ordine e nome dell'etichetta non rilevanti, possono essere presenti ulteriori colonne):
## importo: importo in euro
## codice_avviso: codice completo dell'avviso (17 cifre)
## causale: causale completa
## codiceidentificativoPagatore: codice fiscale del debitore
## identificativoServizio: codice identificativo del servizio di incasso
## dataScadenza: data di scadenza dell'avviso
## il codice identificativo del servizo di di incasso è sciolto nella sua denominazione completa tramite il file serviziDiIncasso.py
## Il file CSV con i dati è passato come argomento da linea di comando
## Il programma guida attraverso i seguenti passaggi:
## 1. converte CSV in tabella di lavoro e crea un JSON con gli stessi dati (TIMESTAMP - Lotto)
## 2. controlla lo stato di sottoscrizione dei codici fiscali presenti nel CSV e crea tabella di alvoro e JSON con 4 liste: iscritti, non iscritti, senza IO, non verificabili. Crea un JSON con il riusltato dell'interrogazione (TIMESTAMP - RisultatoCF)
## 3. invia il messaggio IO ai codici fiscali iscritti e crea un JSON con gli esiti (TIMESTAMP - EsitoInvii)
## 4. crea un file di log TIMESTAMP - Lotto.log con le operazioni salienti (già mostrate a video durante l'esecuzione).
## Tutte le operazioni e le interazioni con le API di IO sono annotate nel log appIO.log

## Il testo del messaggio IO è definito in preparaDati.py

import preparaDati
import parlaConIO
import serviziIO
import serviziDiIncasso
import csv
import sys
import os.path
import os

###import per annotare il log di requests
import logging
from http.client import HTTPConnection  # py3
log = logging.getLogger('urllib3')
log.setLevel(logging.DEBUG)

listaOK = preparaDati.listaOK ##risposte da interpretare come sì
crea = preparaDati.crea_body_avviso_pagamento ##indicare qui la funzione per la creazione del body del messaggio
##corrispondenzeDiDefault = {} ##questo dizionario DEVE essere sempre presente (eventualmente vuoto)
corrispondenzeDiDefault = {'codice_servizio_incasso': 'identificativoServizio', 'causale': 'causaleDebito', 'importo': 'Importo', 'codice_avviso': 'codiceAvviso', 'scadenza': 'dataScadenza', 'email': 'e-mailPagatore', 'codiceFiscale': 'codiceidentificativoPagatore'}
data_lotto = preparaDati.timestamp()

## Selezione del servizio IO da utilizzare
print("Questi sono i servizi IO attualmente configurati per inviare richieste di pagamento:")
for chiave in serviziIO.elencoServiziIOPagabili:
   print(chiave, ":", serviziIO.serviziIO[chiave]["nome"])
servizio = input("Quale servizio IO vuoi utilizzare? Indica il codice fra quelli elencati sopra: ")
if servizio in serviziIO.elencoServiziIOPagabili:
   servizioIO=servizio
else:
   servizio = input("Servizio non valido, ritenta. Indica il codice fra quelli elencati sopra: ")
   if servizio in serviziIO.elencoServiziIOPagabili:
      servizioIO = servizio
   else:
      print("Servizio indicato non valido.")
      q = input("Premi INVIO/ENTER per terminare l'esecuzione del programma.")
      print("Programma terminato.")
      exit()

## Inizializzazione di cartella di lotto, file di output e logging
path=preparaDati.crea_cartella(servizioIO, data_lotto) # crea la cartella di lavoro del lotto
lottoLog=path + data_lotto + "-" + "Lotto.log"
lottoJson=path + data_lotto + "-" + "Lotto.json"
erroriCSV = path + data_lotto + "-" + "ErroriCSV.csv"
risultatoCFJson=path + data_lotto + "-" + "RisultatoCF.json"
esitoInviiJson=path + data_lotto + "-" + "EsitoInvii.json"
requestsLog = path + data_lotto + "-" + "Requests.log"
fh = logging.FileHandler(requestsLog)
log.addHandler(fh)

# definisco la funzione stampa da usare al posto di print per scrivere il messaggio anche sul file Lotto.log - POI studaire un sistema migliore!!
def stampa(stringa):
   print(stringa)
   with open(lottoLog, 'a+') as fileLog:
      rigaDiLog=[preparaDati.timestamp(),stringa]
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
      stampa("Per favore indicalo nel seguente modo: python inviaLottoAvvisiDiPagamento.py <nomeDelTuoFile.csv>")
      q = input("Premi INVIO/ENTER per terminare.")
      stampa("Programma terminato.")
      exit()
elif os.path.exists("EstrazioneDovuti.csv"):
   usa_default = input("Non hai indicato il file con i dati da processare. \nHo trovato il file EstrazioneDovuti.csv. Vuoi usare questo? (Sì/No): ")
   if usa_default in listaOK:
         stampa("OK, proseguo con questo file.")
         nomeFileDati = "EstrazioneDovuti.csv"
   else:
         stampa("Per favore indica il file con i dati da processare nel seguente modo:")
         stampa("python inviaLottoAvvisiDiPagamento.py <nomeDelTuoFile.csv>")
         q = input("Premi INVIO/ENTER per terminare.")
         stampa("Programma terminato.")
         exit()
else:
   stampa("Non hai indicato il file CSV con i dati da processare. Per favore indicalo nel seguente modo:")
   stampa("python inviaLottoAvvisiDiPagamento.py <nomeDelTuoFile.csv>")
   q = input("Premi INVIO/ENTER per terminare.")
   stampa("Programma terminato.")
   exit()

# sezione per l'elaborazione del CSV con i dati da processare e creazione di tabella e JSON
(tabellaDati, tabellaErrori, righeErrori) = preparaDati.importa_da_csv(nomeFileDati)
if tabellaDati==[]:
    print("niente da elaborare, ciao.")
    q = input("Premi INVIO/ENTER per terminare.")
    stampa("Programma terminato.")
    exit()
else:
   etichetteCSV = list(tabellaDati[0].keys())
preparaDati.esporta_json(tabellaDati, lottoJson, data_lotto)
stampa("CSV elaborato. Il file JSON " + lottoJson + " contiene i dati estratti.")

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
   stampa("Ho individuato le seguenti corrispondenze:")
   stampa(str(corrispondenzeDiDefault))
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
stampa("In base alle tue indicazioni, ho individuato le corrispondenze come nel seguente esempio:")
stampa(str(parametriDiEsempio))
payloadDiEsempio = crea(**parametriDiEsempio)
stampa("In base alle tue indicazioni, il messaggio risulta formato come segue:")
stampa(str(payloadDiEsempio))
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
    cf = riga[corrispondenze["codiceFiscale"]]
    if cf:
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
if len(risultato["iscritti"]) == 0:
    stampa("Nessun messaggio da inviare, ciao.")
    invii = ["Nessun messaggio inviato."] #migliorare, perche' cosi' ho un json non omogeneo con gli altri
    preparaDati.esporta_json(invii, esitoInviiJson, data_lotto)
    q = input("Premi INVIO/ENTER per terminare")
    exit()
else:
    for riga in tabellaDati:
        if riga[corrispondenze["codiceFiscale"]] in risultato["iscritti"]:
            parametri = {}
            for i in argomenti:
               parametri[i] = riga[corrispondenze[i]]
            payload = crea(**parametri)
            timestamp_submit=preparaDati.timestamp()
            messaggio = parlaConIO.submitMessage(riga[corrispondenze["codiceFiscale"]], servizioIO, payload)
            print(payload)
            print(messaggio)
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
            else:
               invio["esito"] = "Non accettato"
               invio["motivo"] = messaggio.json()["title"]
            invii.append(invio)
        else:
            print("utente non iscritto")

preparaDati.esporta_json(invii, esitoInviiJson, data_lotto)

stampa("Invio del lotto di messaggi terminato.")
stampa("Invii tentati: " + str(len(invii)) + ".")
a = sum([1 for i in invii if i["status_code"] == 201])
stampa("Invii accettati: " + str(a) + ".")
stampa("Consulta il file JSON " + esitoInviiJson + " per i dettagli dei singoli invii.")
q = input("Premi INVIO/ENTER per terminare")
exit()
