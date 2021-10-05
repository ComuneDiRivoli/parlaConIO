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


## Lo script consente di verificare lo stato di consegna dei messaggi di un lotto precedentemente inviato
## Richiede come argomento in input il file <TIMESTAMP>-EsitoInvii.json presente nella cartella del lotto da verificare
## L'esito della verifica è mostrato a video e memorizzato in file nella cartella di lotto
## Durante la verifica i messaggi con primo invio fallito sono inviati nuovamente

import parlaConIO
import preparaDati
import json
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

# il programma attende di avere come argomento il nome del file JSON \'EsitoInvii\' con i dati del lotto da verificare. Se indicato ne controlla l'esistenza; se non indicato invita a riprovare
if len(sys.argv) > 1:
   if os.path.exists(sys.argv[1]):
      print("File "+sys.argv[1]+" trovato.")
      proseguire = input("Si raccomanda di eseguire la verifica almeno un'ora dopo la fine dell'invio del lotto. Proseguire? (Sì/No) :")
      if proseguire in listaOK:
         print("OK, proseguo.")
         nomeFileEsiti = sys.argv[1]
      else:
          q = input("Premi INVIO/ENTER per terminare")
          print("Programma terminato.")
          exit()
   else:
      print("File di input non valido.")
      print("Per favore indicalo nel seguente modo: python verificaConsegnaLotto.py <nomeDelTuoFile.json>")
      q = input("Premi INVIO/ENTER per terminare.")
      stampa("Programma terminato.")
      exit()
else:
   print("Non hai indicato il file JSON con i dati del lotto da verificare. Per favore indicalo nel seguente modo:")
   print("python verificaConsegnaLotto.py <nomeDelTuoFile.json>")
   q = input("Premi INVIO/ENTER per terminare.")
   print("Programma terminato.")
   exit()

   
secondoGiroInvii = []

with open(nomeFileEsiti, "r") as esiti:
	tabellaEsiti = json.load(esiti)

data_lotto = tabellaEsiti[0]["dataLotto"]
servizioIO = tabellaEsiti[0]["servizioIO"]
path = preparaDati.crea_cartella(servizioIO, data_lotto) # crea/verifica la cartella di lavoro del lotto
verificaLottoLog = path + data_lotto + "-" + "VerificaLotto.log"
statoPrimaConsegnaJson = path + data_lotto + "-" + "StatoPrimaConsegna.json"
secondoGiroInviiJson = path + data_lotto + "-" + "SecondoGiroInvii.json"
requestsLog = path + data_lotto + "-" + "Requests.log"

fh = logging.FileHandler(requestsLog)
log.addHandler(fh)
 
# definisco la funzione stampa da usare al posto di print per scrivere il messaggio anche sul file Lotto.log - POI studaire un sistema migliore!!
def stampa(stringa):
   print(stringa)
   with open(verificaLottoLog, 'a+') as fileLog:
      rigaDiLog=[preparaDati.timestamp(),stringa]
      fileLog.write(";".join(rigaDiLog))
      fileLog.write("\n")
      fileLog.flush()

stampa("Ciao " + os.getlogin() + "!")
stampa("Inizio la verifica del lotto creato il "+str(data_lotto)+".")

if os.path.exists(secondoGiroInviiJson):
   with open(secondoGiroInviiJson, "r") as file:
      x = json.load(file)
   if len(x) > 0:
      stampa("ATTENZIONE: sembra che questo lotto sia già stato verificato.")
      stampa("Nella precendente verifica sono stati inviati nuovamente " + str(len(x)) + " messaggi.")
      stampa("Se prosegui questi messaggi saranno inviati ancora una volta!")
      continua = input("Sei sicuro di voler proseguire? (Sì/No): ")
      if continua not in listaOK:
         q = input("Premi INVIO/ENTER per terminare.")
         print("Programma terminato.")
         exit()
      
for riga in tabellaEsiti:
    if riga["status_code"] == 201:
        stampa("Messaggio " + riga["id"] + " accettato: verifico stato.")
        statoMessaggio = parlaConIO.getMessage(riga["codiceFiscale"], riga["id"], riga["servizioIO"])
        print(statoMessaggio.json())
        riga["created_at"] = statoMessaggio.json()["message"]["created_at"]
        riga ["sender_service_id"] = statoMessaggio.json()["message"]["sender_service_id"]
        riga["statoConsegna"] = statoMessaggio.json()["status"]
        stampa("Messaggio "+riga["esito"]+ " in stato "+riga["statoConsegna"]+".")
        if statoMessaggio.json()["status"] in ["REJECTED", "FAILED"]: #fai un nuovo invio
            stampa("Messaggio "+riga["id"]+ " in stato "+riga["statoConsegna"] + " accettato ma non consegnato: invio nuovamente.")
            timestamp_submit=preparaDati.timestamp()
            messaggio = parlaConIO.submitMessage(riga["codiceFiscale"], riga["servizioIO"], riga["testo"])
            stampa(messaggio)
            invio={}
            invio["timestamp"]=str(timestamp_submit)
            invio["dataLotto"]=data_lotto
            invio["servizioIO"]=servizioIO
            invio["codiceFiscale"]=riga["codiceFiscale"]
            invio["testo"]=riga["testo"]
            invio["status_code"]=messaggio.status_code
            if messaggio.status_code == 201:
               invio["esito"] = "Accettato"
               invio["id"] = messaggio.json()["id"]
            else:
               invio["esito"] = "Non accettato"
               invio["motivo"] = messaggio.json()["title"]
            secondoGiroInvii.append(invio)
    else: #annota primo invio fallito e fai un nuovo invio
        riga["statoConsegna"]="Primo invio fallito"
        stampa("Messaggio prodotto il "+riga["timestamp"] +" con primo invio fallito: invio nuovamente.")
        timestamp_submit=preparaDati.timestamp()
        messaggio = parlaConIO.submitMessage(riga["codiceFiscale"], riga["servizioIO"], riga["testo"])
        stampa(messaggio)
        invio={}
        invio["timestamp"]=str(timestamp_submit)
        invio["dataLotto"]=data_lotto
        invio["servizioIO"]=riga["servizioIO"]
        invio["codiceFiscale"]=riga["codiceFiscale"]
        invio["testo"]=riga["testo"]
        invio["status_code"]=messaggio.status_code
        if messaggio.status_code == 201:
            invio["esito"] = "Accettato"
            invio["id"] = messaggio.json()["id"]
        else:
            invio["esito"] = "Non accettato"
            invio["motivo"] = messaggio.json()["title"]
        secondoGiroInvii.append(invio)

stampa("Verifica terminata. Per eventuali messaggi precedentemente non inviati o consegnati ho eseguito un secondo invio.")
stampa("Invii controllati: " + str(len(tabellaEsiti)))
a = sum([1 for i in tabellaEsiti if i["status_code"] == 201])
stampa("Messaggi accettati nel primo invio: " + str(a) + ".")
b = sum([1 for i in tabellaEsiti if i["statoConsegna"] == "PROCESSED"])
stampa("Messaggi accettati e consegnati nel primo invio: " + str(b) + ".")
c = sum([1 for i in tabellaEsiti if i["statoConsegna"] in ["REJECTED", "FAILED"]])
stampa("Messaggi accettati ma NON consegnati nel primo invio: " + str(c) + ".")
d = sum([1 for i in tabellaEsiti if i["esito"] == "Non accettato"])
stampa("Messaggi NON accettati nel primo invio: " + str(c) + ".")
stampa("Messaggi nuovamente inviati: " + str(len(secondoGiroInvii)) + ".")

preparaDati.esporta_json(tabellaEsiti, statoPrimaConsegnaJson, data_lotto)
preparaDati.esporta_json(secondoGiroInvii, secondoGiroInviiJson, data_lotto)

stampa("Trovi i dettagli della verifica e del secondo invio nei file JSON " + statoPrimaConsegnaJson + " e " + secondoGiroInviiJson + ".")
stampa("Tutti i file di resoconto di questo lotto di invii si trovano nella cartella " + path + ".")
q = input("Premi INVIO/ENTER per terminare.")
stampa("Programma terminato.")
exit()
