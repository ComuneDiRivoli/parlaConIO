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

## Verificare gli iscritti a un servizio IO a partire da una lista di codici fiscali
## I dati per la verifica sono sono contenuti in un CSV (con delimitatore ;) in cui una colonna (da indicare) contiene il codice fiscale


## Il file CSV con i dati è passato come argomento da linea di comando
## Il programma guida attraverso i seguenti passaggi:
## 1. converte CSV in tabella di lavoro
## 2. controlla lo stato di sottoscrizione dei codici fiscali presenti nel CSV e crea tabella di alvoro e JSON con 4 liste: iscritti, non iscritti, senza IO, non verificabili. Crea un JSON con il riusltato dell'interrogazione (TIMESTAMP - RisultatoCF)
## 3. crea un file di log TIMESTAMP - Lotto.log con le operazioni salienti (già mostrate a video durante l'esecuzione).
## Tutte le operazioni e le interazioni con le API di IO sono annotate nel log appIO.
## Il log delle azioni del modulo requests (dialogo con web service remoto) sono annotate in apposito log nella cartella di lotto.

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

listaOK = preparaDati.listaOK ##risposte da interpretare come sì
data_lotto = preparaDati.timestamp()

## Selezione del servizio IO da utilizzare
print("Questi sono i servizi IO attualmente configurati:")
for chiave in serviziIO.elencoServiziIO:
   print(chiave, ":", serviziIO.serviziIO[chiave]["nome"])
servizio = input("Per Quale servizio IO vuoi verificare l'iscrizione? Indica il codice fra quelli elencati sopra: ")
if servizio in serviziIO.elencoServiziIO:
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
path = preparaDati.crea_cartella("verificaCF-"+servizioIO, data_lotto) # crea la cartella di lavoro del lotto
lottoLog = path + data_lotto + "-" + "Lotto.log"
#lottoJson = path + data_lotto + "-" + "Lotto.json"
erroriCSV = path + data_lotto + "-" + "ErroriCSV.csv"
risultatoCFJson = path + data_lotto + "-" + "RisultatoCF.json"
requestsLog = path + data_lotto + "-" + "Requests.log"
nonElaborati = path + data_lotto + "-" + "datiNonElaborati.csv"
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

stampa("Ciao " + os.getlogin() + "!")

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
      stampa("Per favore indicalo nel seguente modo: py \[python\] verificaListaCF.py <nomeDelTuoFile.csv>")
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
         stampa("py \[python\] verificaListaCF.py <nomeDelTuoFile.csv>")
         q = input("Premi INVIO/ENTER per terminare.")
         stampa("Programma terminato.")
         exit()
else:
   stampa("Non hai indicato il file CSV con i dati da processare. Per favore indicalo nel seguente modo:")
   stampa("py \[python\] verificaListaCF.py  <nomeDelTuoFile.csv>")
   q = input("Premi INVIO/ENTER per terminare.")
   stampa("Programma terminato.")
   exit()



#sezione per l'elaborazione del CSV con i dati da processare
stampa("Importo i codici fiscali dal file CSV fornito.")
(tabellaDati, tabellaErrori, righeErrori) = preparaDati.importa_da_csv(nomeFileDati)

if tabellaDati == []:
    stampa("Niente da elaborare, ciao.")
    q = input("Premi INVIO/ENTER per terminare.")
    stampa("Programma terminato.")
    exit()
else:
    chiaviCSV = list(tabellaDati[0].keys())

if len(tabellaErrori) > 1:
   preparaDati.esporta_csv(tabellaErrori, erroriCSV, data_lotto)
   stampa("ATTENZIONE: il CSV contiene almeno una riga con errori. Ho ignorato queste righe e le ho raccolte nel file " + erroriCSV + ".")
   stampa("Le righe del CSV con errori sono le seguenti: " + str(righeErrori))
   q = input("Premi INVIO/ENTER per proseguire")

print("Il CSV importato ha le seguenti chiavi:")
for i in chiaviCSV:
   print(i)
chiaveCF = input("Indicare la chiave che contiene il codice fiscale: ")
while not chiaveCF in chiaviCSV:
   chiaveCF = input("Indicare la chiave che contiene il codice fiscale: ")

prosegui = input("Proseguo con il controllo dell'iscrizione degli utenti al servizio " + serviziIO.serviziIO[servizioIO]["nome"] +"? (Sì/No): ")
if prosegui not in listaOK:
   q = input("Premi INVIO/ENTER per terminare.")
   stampa("Programma terminato.")
   exit()
else:
   stampa("Controllo lo stato di iscrizione al servizio " + serviziIO.serviziIO[servizioIO]["nome"])

dizionarioCodiciFiscaliUtenti={} #serve per eliminare i codici fiscali presenti più volte

for riga in tabellaDati:
    cf = riga[chiaveCF]
    if cf:
       dizionarioCodiciFiscaliUtenti[cf]=""
listaCodiciFiscaliUtenti = list(dizionarioCodiciFiscaliUtenti.keys())

(risultato, codaNonElaborata) = parlaConIO.controllaCF(listaCodiciFiscaliUtenti, servizioIO)

if codaNonElaborata:
   stampa("ATTENZIONE: l'interrogazione si è interrotta per sovraccarico del server IO.")    
stampa("Codici fiscali elaborati = "+str(len(listaCodiciFiscaliUtenti)-len(codaNonElaborata)))
stampa("Utenti con app IO iscritti = "+str(len(risultato["iscritti"])))
stampa("Utenti con app IO non iscritti = "+str(len(risultato["nonIscritti"])))
stampa("Utenti senza app IO = "+str(len(risultato["senzaAppIO"])))
stampa("Errori di interrogazione = "+str(len(risultato["inErrore"])))
stampa("Trovi il risultato dell'interrogazione delle iscrizioni al servizio nel file JSON " + risultatoCFJson + ".")
if codaNonElaborata:
   stampa("Codici fiscali non elaborati = "+str(len(codaNonElaborata)))
   stampa("Trovi i codici fiscali non elaborati nel file " + nonElaborati + ".")
   stampa("Per completare l'interrogazione esegui nuovamente il programma con quel file come input.")
   preparaDati.esporta_lista_csv(codaNonElaborata, chiaveCF, nonElaborati, data_lotto)
preparaDati.esporta_json(risultato, risultatoCFJson, data_lotto)

q = input("Premi INVIO/ENTER per terminare")
exit()
