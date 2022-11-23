##definisce la tabella dei servizi IO attivi (codice, nome, API KEY e altri attributi utili per la gestione)

##NON USARE LETTERE ACCENTATE E CARATTERI SPECIALI, per scrivere un apostrofo ' fargli precedere una barra \, cioè scrivere \'


##per ogni servizio presente su IO aggiungere le seguenti righe righe:
##serviziIO["CODICE"]={}
##serviziIO["CODICE"]["APIKEY"]="APIKEY primaria (da backoffice IO)"
##serviziIO["CODICE"]["APIKEY2"]="APIKEY secondaria(da backoffice IO)"
##serviziIO["CODICE"]["ID"]="ID del servizio in IO"
##serviziIO["CODICE"]["nome"]="Descrizione del servizio (come da backoffice IO, ma non fondamentale)"
##serviziIO["CODICE"]["pagabile"]="Sì"  ##indicare "Sì"/"No" se il servizio è abilitato a veicolare pagamenti (da backoffice IO)
##serviziIO["CODICE"]["testoFisso"]="No"   ##indicare "Sì"/"No" se di intende utilizzare il servizio IO anche per messaggi con testo fisso senza variabili


serviziIO={}
serviziIO["AP"]={}
serviziIO["AP"]["APIKEY"]="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
serviziIO["AP"]["APIKEY2"]="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
serviziIO["AP"]["ID"]="xxxxxxxxxxxxxxxxxxxxxxxxxx"
serviziIO["AP"]["nome"]="Avviso di pagamento"
serviziIO["AP"]["pagabile"]="Sì"
serviziIO["AP"]["testoFisso"]="No"
serviziIO["SCI"]["APIKEY"]="******TUAKEY1*****"
serviziIO["SCI"]["APIKEY2"]="******TUAKEY2*****"
serviziIO["SCI"]["ID"]="xxxxxxxxxxxxxxxxxxxxxxxxxx"
serviziIO["SCI"]["nome"]="Promemoria di scadenza della carta d'identità"
serviziIO["SCI"]["pagabile"]="No"
serviziIO["SCI"]["testoFisso"]="No"
