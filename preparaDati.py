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

## Definisce le operazioni utili alla preparazione dei messaggi verso app IO

## ATTENZIONE: prima dell'uso individuare le occorrenze della stringa XXXXXX e personalizzare di conseguenze

import csv
import json
import datetime
import os
import os.path
import inspect
import serviziDiIncasso

listaOK = ["sì", "SI", "S", "s", "Sì", "OK", "si"] # elenco di parola da interpretare come risposta affermativa in caso di domanda posta dal programma

def attendi():
    q = input("Premi INVIO/ENTER per proseguire.")

def termina():
    q = input("Premi INVIO/ENTER per terminare.")
    exit()

def scegli(domanda):
    q = input(domanda)
    if q in listaOK:
        risposta = True
    else:
        risposta = False
    return risposta
    
   
def timestamp(): #definisco il timestamp da inserire nei log
    return datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')

def data(data): #converte uan stringa che indica una data nel forma gg/mm/aaaa nel formato ISO 8601 (richiesto dalle API IO) - viene 
    str = data
    date_object = datetime.datetime.strptime(str, "%d/%m/%Y")
    return date_object.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    
def importa_da_csv(nomefile):
    with open(nomefile, "r") as csvfile:
        fonte = csv.reader(csvfile, delimiter=";")
        righe=list(fonte)
        #righe=[]
        #for riga in fonte:
        #    righe.append(riga)
        etichette=righe[0] #estraggo i nomi dei campi dalla prima riga del csv
        tabella = []
        tabellaErrori = [etichette]
        righeErrori = []
        for i in range(1,len(righe)): #per ogni riga del csv iniziale creo un dizionario di nome record
            if len(righe[i]) == len(etichette):
                record={}
                for j in range(0,len(etichette)): #per ogni etichetta del csv creo una voce del dizionario record
                    record[etichette[j]]=righe[i][j]
                tabella.append(record) #accodo il dizionario record alla tabella
            else:
                print("Qualcosa non va alla riga", i+1, "del CSV")
                tabellaErrori.append(righe[i])
                righeErrori.append(i+1)
    return (tabella, tabellaErrori, righeErrori)


def crea_cartella(suffisso, dataeora=""): # crea cartella con nome "dataeora-suffisso"
    x = timestamp() if dataeora=="" else dataeora
    path="./" + dataeora + "-" + suffisso + "/"
    if not os.path.isdir(path):
        os.mkdir(path)
    return path

##def esporta_json(tabella, nomefile, dataeora=""):
##    x = timestamp() if dataeora=="" else dataeora
##    with open(x + "-" + nomefile+".json", 'w+') as file:
##        file.write(json.dumps(tabella, sort_keys=False, indent=4))

##funzione per esportare una lista di dizionari in file JSON
def esporta_json(tabella, destinazione, dataeora=""): # destinazione è il percorso completo del file
    #x = timestamp() if dataeora=="" else dataeora
    with open(destinazione, 'w+') as file:
        file.write(json.dumps(tabella, sort_keys=False, indent=4))

## funzione per esportae una lista di liste (tabella) in csv
def esporta_csv(tabella, destinazione, dataeora=""): # destinazione è il percorso completo del file
    #x = timestamp() if dataeora=="" else dataeora
    with open(destinazione, 'w', newline='') as file:
        erroriwriter = csv.writer(file, delimiter=";")
        for i in range(0,len(tabella)):
            erroriwriter.writerow(tabella[i])
            #file.write(";".join(tabella[i]))
            #file.write("\n")

## funzione per esporta una lista semplice in file csv con una solo colonna e etichetta "primariga"
def esporta_lista_csv(lista, primariga, destinazione, dataeora=""): # destinazione è il percorso completo del file
    with open(destinazione, 'w', newline='') as file:
        file.write(primariga)
        file.write("\n")
        for i in lista:
            file.write(i)
            file.write("\n")
                
## la funzione "mappa" consente di associare i valori della lista "argomenti" a quelli della lista "etichette"
## serve per indicare quali colonne di un CSV di dati in input sono da usare come argomenti della funzione che crea il body del messaggio da inviare
## se le due liste hanno elementi uguali, l'associzione è proposta di defualt
## il dizionario utilizzato come risultato puo' essere usato per passare i parametri alla funzione: funzione(**dizionario)
	
def mappa(argomenti, etichette):
    corrispondenze = {}
    for i in argomenti:
        corrispondenze[i] = ''
    for i in argomenti:
        if i in etichette:
            corrispondenze[i] = i
    print("-------- \nGli ARGOMENTI richiesti dalla funzione sono:")
    for i in argomenti:
        print(i)
    print("-------- \nLe ETICHETTE disponibili sono:")
    for i in etichette:
        print(i)
    print("-------- \nPer ogni argomento indica l'etichetta da utilizzare (INVIO per confermare la proposta)")
    for i in argomenti:
        if corrispondenze[i]:
            e = input("Indicare l'etichetta da associare all'argomento '" + i + "' (INVIO per '" + corrispondenze[i] + "'): ")
            if not e:
                print("Proposta confermata")
            elif e in etichette:
                corrispondenze[i] = e
            else:
                while bool(e in etichette) == False:
                    e = input("Etichetta non valida. Indicare l'etichetta da associare all'argomento '" + i + "': ")
                corrispondenze[i] = e
        else:
            e = input("Indicare l'etichetta da associare all'argomento '" + i + "': ")
            if e in etichette:
                corrispondenze[i] = e
            else:
                while bool(e in etichette) == False:
                    e = input("Etichetta non valida. Indicare l'etichetta da associare all'argomento '" + i + "': ")
                corrispondenze[i] = e
    return corrispondenze

def recuperaArgomenti(funzione): #crea lista di argomenti con keyword attesi da una funzione (da usare in combinazione con "mappa")
    argomenti = inspect.getfullargspec(funzione).args
    return argomenti



# qui si definiscono le regole (template) per creare i body/payload dei messaggi IO a partire dai CSV prodotti dagli applicativi del sistema informativo comunale


## TEMPLATE GENERICO
## attenzione alle interruzioni di riga: si ottengono con doppio spazio seguito da interruzione di linea. Esempio. "Riga di testo dopo la quale andare a capo.  " + "\n"
## Il nuovo paragrafo (con linea vuota) si ottiene con '\n \n' nella stringa.
def crea_body(nome_servizio, causale, importo, codice_avviso, scadenza, email, codiceFiscale):
    markdown = "Ti informiamo che è stato emesso un avviso di pagamento a tuo nome per il servizio "+nome_servizio+",\n \n Causale: "+causale+"\n \nImporto: "+str(importo)+"\n \nPuoi procedere al pagamento dell’avviso direttamente dalla app IO con l'apposito tasto.  \n  \nIn alternativa, puoi pagare o scaricare l’avviso in formato PDF per il pagamento sul territorio nella pagina [Pagamenti Online](https://LINKPORTALEPAGAMENTI) sul sito del Comune di NOMECOMUNE. Da lì potrai visualizzare anche lo storico dei tuoi pagamenti verso il Comune e prelevare le ricevute."
    payment_data={}
    payment_data["amount"] = int(float(importo)*100)
    payment_data["notice_number"] = "3"+codice_avviso
    payment_data["invalid_after_due_date"] = False
    body={}
    body["time_to_live"] = 3600
    body["content"] = {"subject":"Avviso di pagamento", "markdown":markdown, "payment_data":payment_data, "due_date": str(data(scadenza))}
    # body["default_addresses"]={"email":email}
    body["fiscal_code"]=codiceFiscale
    return body


## Servizio IO "Avviso di pagamento" - a partire dal CSV estratto da software dei pagamenti pagoPA
def crea_body_avviso_pagamento(codice_servizio_incasso, causale, importo, codice_avviso, scadenza, email, codiceFiscale):
    if codice_servizio_incasso in serviziDiIncasso.elencoServiziDiIncasso:
        nome_servizio = str(serviziDiIncasso.serviziDiIncasso[codice_servizio_incasso]["nome"])
    else:
        nome_servizio = "---"
    markdown = "Ti informiamo che è stato emesso un avviso di pagamento a tuo nome per il servizio **"+nome_servizio+"**,  " + "\n" + "**Causale**: " + causale + "  " + "\n" + "**Importo**: euro " + str(importo) + "\n \nPuoi procedere al pagamento dell’avviso direttamente dalla app IO con l'apposito tasto. \n \nIn alternativa, puoi pagare o scaricare l’avviso in formato PDF per il pagamento sul territorio nella pagina [Pagamenti Online](https://LINKPORTALEPAGAMENTI) sul sito del Comune di NOMECOMUNE. Da lì potrai visualizzare anche lo storico dei tuoi pagamenti verso il Comune e prelevare le ricevute."
    payment_data={}
    payment_data["amount"] = int(float(importo)*100)
    payment_data["notice_number"] = str(codice_avviso)
    payment_data["invalid_after_due_date"] = False
    body={}
    body["time_to_live"] = 3600
    body["content"] = {"subject":"TEST - Avviso di pagamento", "markdown":markdown, "payment_data":payment_data, "due_date": str(data(scadenza))}
    body["fiscal_code"]=codiceFiscale
    return body

## creazione di un messaggio per promemoria scadenza carta di identità a partire da csv con colonna codiceFiscale e dataScadenzaDocumento
def crea_body_scadenzaCI(dataScadenzaDocumento, codiceFiscale):
    markdown = "Ti informiamo che **la tua carta di identità scade il giorno " + dataScadenzaDocumento + "**. Puoi prenotare l'appuntamento per l'emissione di una nuova carta d'identità elettronica utlizzando il servizio online [Prenota un appuntamento](https://LINKAGENDA) sul sito del Comune di NOMECOMUNE."
    body={}
    body["time_to_live"] = 3600
    body["content"] = {"subject": "TEST - La tua carta di identità scade a breve", "markdown": markdown}
    body["fiscal_code"]=codiceFiscale
    return body

## Creazione di un messaggio con testo fisso
def crea_body_testoFisso(titolo, testoFisso, codiceFiscale):
    body={}
    body["time_to_live"] = 3600
    body["content"] = {"subject": titolo, "markdown": testoFisso}
    body["fiscal_code"] = codiceFiscale
    return body
