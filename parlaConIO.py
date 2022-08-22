import requests
import socket
import datetime
import json
import time
import os
import serviziIO

# import logging

cftest="AAAAAA00A00A000A" ## codice fiscale di test in ambiente IO
baseURL = "https://api.io.pagopa.it/api/v1" # url di base dei web service IO

logFileName="appIO.log"


# logging.basicConfig(level=logging.DEBUG)

def getIPAddress():
    return socket.gethostbyname(socket.gethostname())

callingIP = getIPAddress()
callingUser = os.getlogin()

def timestamp():
    return datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')

def logRequest(logFile, requestTime, verbo, metodo, info):
    rigaDiLog=[requestTime, callingIP, callingUser, verbo, metodo, info]
    logFile.write(";".join(rigaDiLog))
    logFile.write("\n")
    logFile.flush()

def logResponse(logFile, responseTime, requestTime, status_code, info):
    rigaDiLog=[responseTime, callingIP, requestTime, str(status_code), info]
    logFile.write(";".join(rigaDiLog))
    logFile.write("\n")
    logFile.flush()

def getProfile(codiceFiscale, servizioIO):
    headers={"Ocp-Apim-Subscription-Key":serviziIO.serviziIO[servizioIO]["APIKEY"]}
    with open(logFileName, "a+") as logFile:
        requestTime=timestamp()
        logRequest(logFile, requestTime, "GET", "profiles", codiceFiscale)
        r = requests.get(baseURL+"/profiles/"+codiceFiscale, headers = headers, timeout=100)
        responseTime=timestamp()
        info = str(r.json()["sender_allowed"]) if r.status_code==200 else str(r.json()["title"])
        logResponse(logFile, responseTime, requestTime, r.status_code, info)
        return r

def getProfilePost(codiceFiscale, servizioIO):
    headers={"Ocp-Apim-Subscription-Key":serviziIO.serviziIO[servizioIO]["APIKEY"]}
    with open(logFileName, "a+") as logFile:
        requestTime=timestamp()
        logRequest(logFile, requestTime, "GET", "profiles", codiceFiscale)
        r = requests.post(baseURL+"/profiles", headers = headers, timeout=100, json={"fiscal_code" : codiceFiscale})
        responseTime=timestamp()
        info = str(r.json()["sender_allowed"]) if r.status_code==200 else str(r.json()["title"])
        logResponse(logFile, responseTime, requestTime, r.status_code, info)
        return r

def submitMessage(codiceFiscale, servizioIO, body): #CF nel payload
    headers={"Ocp-Apim-Subscription-Key":serviziIO.serviziIO[servizioIO]["APIKEY"], "Content-Type":"application/json", "Connection":"keep-alive"}
    with open(logFileName, "a+") as logFile:
        requestTime=timestamp()
        logRequest(logFile, requestTime, "POST", "submitMessage", codiceFiscale)
        r = requests.post(baseURL+"/messages", headers = headers, timeout=100, json=body)
        responseTime=timestamp()
        info = str(r.json()["id"]) if r.status_code==201 else str(r.json()["title"])
        logResponse(logFile, responseTime, requestTime, r.status_code, info)
        return r

def submitMessageCF(codiceFiscale, servizioIO, body):   #CF nell'URL
    headers={"Ocp-Apim-Subscription-Key":serviziIO.serviziIO[servizioIO]["APIKEY"], "Content-Type":"application/json", "Connection":"keep-alive"}
    with open(logFileName, "a+") as logFile:
        requestTime=timestamp()
        logRequest(logFile, requestTime, "POST", "submitMessage", codiceFiscale)
        r = requests.post(baseURL+"/messages/"+codiceFiscale, headers=headers, timeout=100, json=body)
        responseTime=timestamp()
        info = str(r.json()["id"]) if r.status_code==201 else str(r.json()["title"])
        logResponse(logFile, responseTime, requestTime, r.status_code, info)
        return r

def getMessage(codiceFiscale, message_id, servizioIO):
    headers={"Ocp-Apim-Subscription-Key": serviziIO.serviziIO[servizioIO]["APIKEY"]}
    with open(logFileName, "a+") as logFile:
        requestTime=timestamp()
        logRequest(logFile, requestTime, "GET", "getMessage", message_id)
        r = requests.get(baseURL+"/messages/"+codiceFiscale+"/"+message_id, headers=headers, timeout=100)
        responseTime=timestamp()
        info = str(r.json()["status"]) if r.status_code==200 else str(r.json()["title"])
        logResponse(logFile, responseTime, requestTime, r.status_code, info)
        return r

def controllaCF(listaCF, servizioIO): ## definizione della funzione per controllare iscrizione di una lista di CF a un servizio
    t = 0 #pausa iniziale fra due iterazioni
    tmax = 0.2 #limite massimo della pausa fra due iterazioni raggiunto il quale si abbandona l'interrogazione
    passo = 0.1 #incremento della pausa fra due iterazioni a ogni errore
    pausa = 3 #pausa una tantum in seguito a errore per server sovraccarico 
    utentiIscritti=[]
    utentiNonIscritti=[]
    utentiSenzaAppIO=[]
    interrogazioniInErrore=[]
    interrogazioniInCoda=[]
    contatore=1
    totale=len(listaCF)
    for cf in listaCF:
        inviato = False
        while not inviato:
            if t >= tmax:
                print("Il sistema è sovraccarico, interrompo l'interrogazione.")
                interrogazioniInCoda = listaCF[listaCF.index(cf):]
                return ({"iscritti":utentiIscritti, "nonIscritti":utentiNonIscritti, "senzaAppIO":utentiSenzaAppIO, "inErrore":interrogazioniInErrore}, interrogazioniInCoda)
            else:
                time.sleep(t)
                print(contatore,"di",totale)
                risposta = getProfilePost(cf, servizioIO)
                if risposta.status_code == 200:
                    if risposta.json()["sender_allowed"]:
                        utentiIscritti.append(cf)
                    else:
                        utentiNonIscritti.append(cf)
                    inviato =  True
                    contatore += 1
                elif risposta.status_code == 429:
                    print("Il server IO è sovraccarico, attendo e inserisco una pausa fra le prossime richieste.")
                    t += passo
                    time.sleep(pausa)
                else:
                    if risposta.status_code == 404:
                        utentiSenzaAppIO.append(cf)
                    else:
                        interrogazioniInErrore.append(cf)
                    inviato = True
                    contatore += 1
            
    return ({"iscritti":utentiIscritti, "nonIscritti":utentiNonIscritti, "senzaAppIO":utentiSenzaAppIO, "inErrore":interrogazioniInErrore}, interrogazioniInCoda)
    

