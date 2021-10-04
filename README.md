# parlaConIO
Inviare messaggi tramite app IO a partire da dati contenuti in file .csv

Script Python per inviare messaggi verso l'app IO partendo da dati contenuti in file CSV

Il progetto comprende degli script Python per **inviare messaggi verso l'app IO a partire da dati contenuti in file CSV**, tipicamente estratti dai software gestionali in uso presso le amministrazioni. Gli script funzionano da riga di comando e dovrebbero essere indipendenti dal sistema operativo in uso (Windows, Linux).
Le operazioni di composizione e invio dei messaggi sono tracciate e memorizzate su log e file di report in formato testo o json. E' incluso anche uno script per la verifica dell'invio di un lotto (=blocco di messaggi ottenuti a partire da un file CSV con i dati).

Gli script consentono di realizzare un dialogo efficace con le API esposte dal sistema app IO, **senza sostenere costi di integrazione degli applicativi in uso**. Infatti, è sufficiente essere in grado di estrarre dagli applicativi i dati necessari alla composizione dei messaggi secondo un template prestabilito e lanciare lo script. L'assenza di un'interfaccia grafica rende l'uso degli script non eccessivamente "friendly" per gli utenti e si consiglia di riservare l'uso degli script al personale tecnico informatico delle amministrazioni o comunque a utenti esperti. Per ogni lotto, nella stessa directory di installazione, è creata una cartella destinata ad accogliere log e report prodotti durante le fasi di composizione, invio e verifica.

Per utilizzare gli script è necessario installare l'**ambiente Python** (www.python.org) e il **modulo 'requests'** (comando: py/python -m pip install requests). 
Una volta copiati i file di definizione delle funzioni e gli script in una cartella/directory (es.: c:\parlaConIO in ambienti Windows) si lanciano da riga di comando, tipicamente indicando come argomento il file CSV da elaborare. In assenza di argomento o in caso di argomento errato, lo script guida l'utente alla sua corretta invocazione.\
I CSV proposti come modello e le regole per interpretarli al fine di comporre i messaggi (payload dell'interrogazione delle API di IO) sono modellati sulle esigenze del Comune di Rivoli. Tuttavia **è possibile modificare le regole di composizione dei messaggi intervenendo sulle funzioni definite in parloConIO e preparaDati.py e negli script "inviaLotto\*"**. L'ordine delle chiavi nei file CSV non è vincolante e le chiavi necessarie alla composizione del messaggio possono coesistere con altre.

Gli script sono migliorabili e in evoluzione. Al momento mancano meccanismi per la gestione efficiente delle eccezioni durante il dialogo con le API di IO. Per esempio, in caso di mancanza di collegamento di rete, il modulo requests restituisce un'eccezione che causa l'interruzione del programma. In tal caso è necessario interrogare i log per capire se e quali messaggi sono stati inviati, eliminare le relative righe dal CSV e lanciare nuovamente lo script di invio. Un evento del genere non consente nemmeno la corretta verifica dello stato di consegna dei messaggi inviati prima dell'interruzione del programma.

Per richieste di assistenza, suggerimenti, proposte e ogni altra discussione sul progetto si rimanda alla sezione "issues" del repository.

Il progetto è ideato e mantenuto dal Comune di Rivoli, Servzio SIA (Sistemi Informativi e Archivistici) ed è aperto alla collaborazione delle amministrazioni interessate.

- **parlaConIO.py** implementa le funzioni di dialogo con IO con relative API key e di logging. 

- **preparaDati.py** definisce le caratteristiche più legate alle operazioni sui file usati come fonte di dati o template per i messaggi.

- **inviaLotto\*** sono script specifici per l'invio di lotti di messaggi di un determinato servizio IO (indicazioni nel preambolo del codice); dove possibile una procedura interattiva guida nell'associazione fra le "colonne" del file CSV e le variabili presenti nel template del messaggio. Gli script si eseguono indicando come argomento il nome del file csv con i dati da processare. Esempio "py ./inviaLottoScadenzaCI.p ./scadenzaCI.csv".

- **verificaConsegnaLotto.py**: consente di verificare lo stato di consegna di un lotto. Richiede come argomento il file "...-EsitoInvii.json" presente nella cartella di lotto del lotto che si vuole verificare.

**STRUMENTI DI SUPPORTO**, utili a fini statistici e per indirizzare le scelte.

**verificaListaCF.py**: esegue la verifica dell'iscrizione a un servizio IO (proposto fra quelli configurati in parlaConIO.py). In input richiede un CSV con una "colonna" che contiene i codici fiscali di cui verificare l'iscrizione. Durante l'esecuzione chiede di indicare quale chiave del CSV contiene il codice fiscale. Restituisce il risultato nella cartella del lotto (cartella con suffisso "verificaCF-<servizioIO>").

**verificaNucleiIO**: estensione del precedente, controlla inoltre per quanti nuclei familiari è presente almeno una installazione di IO iscritta al servizio indicato. Si tratta di una funzione utile per i comuni, per valutare il livello di diffusione di IO sul proprio territorio. Lo script si attende in input un file CSV con due colonne, la prima con il codice fiscale la seconda con un codice identificativo del nucleo familiare. Il conteggio dei nuclei familiari con IO è annotato nel file di log, che si trova nella cartella del lotto.
  
**FILE DI CONFIGURAZIONE** (i file presenti, per i quali occorre eliminare la stringa "RIMUOVIMI" nel nome del file, sono da personalizzare):
- **serviziIO.py**: contiene le chiavi per i servizi IO configurati nel backoffice di IO e alcuni parametri utili per la gestione dell'operatività
- **serviziDiIncasso.py**: contiene le scioglimento dei codici dei servizi di incasso presenti nell'implementazione PagoPA dell'ente
  
**FILE CSV DI PROVA**: Sono presenti alcuni file CSV di prova con codici fiscali fittizi, alcuni riconosciuti validi da IO e utilizzabili per test (es.: AAAAAA00A00A000A)
