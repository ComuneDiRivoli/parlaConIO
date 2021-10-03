## configurare qui i servizi di incasso PagoPA attivi (se il CSV dei pagamenti da inviare via IO contiene un codice identificativo del servizio, questo file serve per sciogliere il codice
## per ogni servizio aggiungere due righe:
## serviziDiIncasso["CODICE"] = {}
## serviziDiIncasso["CODICE"]["nome"] = "NOME COMPLETO" 

##NON USARE LETTERE ACCENTATE E CARATTERI SPECIALI, per scrivere un apostrofo ' fargli precedere una barra \, cioè scrivere \'


serviziDiIncasso = {}
serviziDiIncasso["TARI"] = {}
serviziDiIncasso["TARI"]["nome"] = "Avvisi di pagamento TARI"


elencoServiziDiIncasso = list(serviziDiIncasso.keys())
