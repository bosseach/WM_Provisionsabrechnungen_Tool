#### Import
import pandas as pd
import sys
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import scrolledtext
import logging
from pathlib import Path

# WMH Module
from core_services.db import execute_sql_query

print("Python verwendet:", sys.executable) # Sicherstellen, dass die venv genutzt wird
Datum=(datetime.now()).strftime("%Y-%m-%d")
Datum_morgen=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")


def starte_GUI():

    #### Funktionen der GUI
    # Custom Logging Handler bilden
    class TextHandler(logging.Handler):
        def __init__(self, text_widget):
            super().__init__()
            self.text_widget = text_widget

        def emit(self, record):
            log_message = self.format(record)
            self.text_widget.insert(tk.END, log_message + "/n")
            self.text_widget.yview(tk.END)  # Scrollt automatisch zum neuesten Eintrag
            self.text_widget.update_idletasks()  # Stellt sicher, dass das GUI live aktualisiert wird

    # Standardfunktionen
    def open_dokumentation():
        text_var=('''1.Importfrunktion: Das Tool reichert eine csv mit den Werbemarkt Daten aus Dialog an und gibt eine fertige csv mit den benötigten Informationen für das Einspielen in Lasernet aus 
        \nHinzugefügte Informationen:
        \n-Steuernummer, Telefon, Telefax, eMail, Brutto, Gesamtbrutto \n(Mapping aus der DOA Datenbank)
        \n-Berechnen des Gesamtbruttowertes pro Gpnr und Rech_Mandant
        \nVorgehen: Über Downloadordner die csv auswählen und starten drücken, Das Tool \nlegt die fertige Lasernet csv im selben Ordner unter dem Namen \n"WM_Provisionsabrechnung_Lasernet_(Datum)" ab
        \nOption: Zusätzliche Excel erstellen, ermöglicht die Daten vor dem Einspielen in Lasernet in einer Excel zu überprüfen
        \n2.Mapping: Ermöglicht das Herunterladen des Mappings der Kundendaten
                  ''')
        # GUI erstellen
        root_doku=tk.Tk()
        root_doku.wm_title('Dokumentation')
        root_doku.geometry("700x400")
        # Text
        doku_tk=tk.Text(root_doku,height=40,width=80)
        doku_tk.grid(row=1,column=0)
        doku_tk.insert(1.0,text_var)
        doku_tk.config(state='disable')

        # Loop
        root_doku.mainloop()

    def browse_file():
            file_path.set(filedialog.askopenfilename())

    def browse_folder():
            folder_path.set(filedialog.askdirectory())

    def start_process(imp):
        logger.info("#### Process gestartet ####")

        ######## Import ########
        #  Import der csv Datei
        df_imp=pd.read_csv(imp,sep=';')
        # Abgleich der csv
        list_col=['Abrechnungs-Monat', 'Rech_Mandant', 'Auftrag-Nr.', 'Inserent',
                'Inserent Name', 'Abrechnung-Nr.', 'Netto', 'Provisionssatz',
                'Provision', 'Abgerechnet am', 'Ausgabe-Nr.', 'Ausgabetext',
                'Gruppe', 'GPNR', 'Firma', 'Straße', 'Hausnr', 'PLZ', 'Ort',
                'Mwst.-Satz', 'Mwst.', 'Leistungsdatum', 'Status'
                ]
        check=0
        for item in list_col:
            if item not in df_imp.columns:
                logger.info(f"\n#### Spalte '{item}' nicht in Import vorhanden ####")
                check=1
        if check==1:
            logger.info("\n#### Bitte überprüfen Sie die Importdatei auf die benötigten Spalten ####")
            return
        else:
             logger.info("\n#### Import gelungen ####")
        
        # Spalten umbennenen
        df_imp=df_imp.rename(columns={'Abrechnungs-Monat':'Abrechnungs_Monat','Ausgabe-Nr.':'Ausgabe_Nr',
                                      'Mwst.-Satz':'Mwst_Satz','Abrechnung-Nr.':'AbrechnungsNr','Mwst.':'MwSt',
                                      'Auftrag-Nr.':'AuftragNr','Inserent Name':'InserentName','Abgerechnet am':'Abgerechnet_Am',
                                      'GPNR':'Gpnr','PLZ':'Plz'
                                      })
        
        ######## Mapping ########
        # SQL Mapping laden
        Query='''
        select *
        from tb_provisionsabrechnung_mapping
        '''
        df_map=execute_sql_query(Query,database='dbm_werbemarkt')

        # Entfernen der Nachkommastellen
        for item in ['Gpnr','Inserent','Hausnr','Plz','Ausgabe_Nr']:
            df_imp[item] = df_imp[item].fillna(0).astype(int)

        # Anpassen der AuftragsNr  
        df_imp['AuftragNr'] = (df_imp['AuftragNr'].str.replace(',00', '', regex=False).astype(str))
        df_imp['AuftragNr'] = (df_imp['AuftragNr'].str.replace('.', '', regex=False).astype(str))
        df_imp['AuftragNr'] = (df_imp['AuftragNr'].str.replace('NaN', '0', regex=False).astype(str))
        df_imp['AuftragNr'] = df_imp['AuftragNr'].fillna(0)
        df_imp['AuftragNr'] = df_imp['AuftragNr'].astype(int)

        # Entfernen potentieller Leerzeichen
        df_imp['Gpnr'] = df_imp['Gpnr'].astype(str)
        df_map['Gpnr'] = df_map['Gpnr'].str.strip()
        df_imp['Rech_Mandant'] = df_imp['Rech_Mandant'].astype(str)
        df_map['Rech_Mandant'] = df_map['Rech_Mandant'].str.strip()
        
        # Mapping durchführen
        df_imp = df_imp.merge(
            df_map[['Gpnr', 'Rech_Mandant', 'Steuernummer', 'Telefon', 'Telefax', 'eMail','Versandart','Kundenmail','Land','Betreff_mail','Absendername']],
            on=['Gpnr', 'Rech_Mandant'],
            how='left'
            )
        logger.info("\n#### Mapping geladen ####")

        ########## Monatsdatum in Betreffzeile erstellen
        monate_de = {
            1: "Januar", 2: "Februar", 3: "März", 4: "April",
            5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
            9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
        }

        # Abrechnungsmonat einmalig in ein Datumsformat umwandeln
        df_imp["Abrechnungs_Monat"] = pd.to_datetime(
            df_imp["Abrechnungs_Monat"],
            format="%d.%m.%Y",
            errors="coerce"
        )

        # DATE je Zeile im Betreff ersetzen
        df_imp["Betreff_mail"] = df_imp.apply(
            lambda row: (
                row["Betreff_mail"].replace(
                    "DATE",
                    f"{monate_de[row['Abrechnungs_Monat'].month-1]} "
                    f"{row['Abrechnungs_Monat'].year}"
                )
                if isinstance(row["Betreff_mail"], str) and "DATE" in row["Betreff_mail"]
                else row["Betreff_mail"]
            ),
            axis=1
        )
        
        ######## Bruttowerte errrechnen ########
        
        # NANs löschen
        df_imp = df_imp.dropna(subset=['Provision'])

        # In englisches Zahlenformat umwandeln
        df_imp['Netto'] = (df_imp['Netto'].str.replace('.', '', regex=False))
        df_imp['Netto'] = (df_imp['Netto'].str.replace(',', '.', regex=False).astype(float))
        df_imp['Provisionssatz'] = df_imp['Provisionssatz'].astype(str)
        df_imp['Provisionssatz'] = (df_imp['Provisionssatz'].str.replace(',', '.', regex=False).astype(float))
        df_imp['MwSt'] = df_imp['MwSt'].astype(str)
        df_imp['MwSt'] = (df_imp['MwSt'].str.replace(',', '.', regex=False).astype(float))
        df_imp['Provision'] = df_imp['Provision'].astype(str)
        df_imp['Provision'] = (df_imp['Provision'].str.replace(',', '.', regex=False).astype(float))

        # Berechnung Einzelwerte. Berechnung der Mwst muss 100% passen => Gerundete Werte aus Dialog nicht genau genug!
        df_imp['MwSt']=df_imp['Provision']*df_imp['Mwst_Satz']/100 
        df_imp['Brutto']=df_imp['Provision']+df_imp['MwSt']
        
        # Gesamtbrutto und Gesamtnetto je Gpnr + Rech_Mandant berechnen
        gesamt_map = (
            df_imp
            .groupby(['Gpnr', 'Rech_Mandant'])[['Brutto', 'Provision','MwSt']]
            .sum()
            .reset_index()
            .rename(columns={
                'Brutto': 'Gesamtbrutto',
                'Provision': 'Gesamtprovision_netto', 
                'MwSt': 'Summe_MwSt'
            })
        )
        
        # Werte zurück auf df_imp mappen
        df_imp = df_imp.merge(
            gesamt_map,
            on=['Gpnr', 'Rech_Mandant'],
            how='left'
        )

        # Runden der Mwst Werte
        df_imp['Summe_MwSt']=df_imp['Summe_MwSt'].round(2)
        df_imp['MwSt']=df_imp['MwSt'].round(2)

        ######## Prüfung AbrechnungsNr. ########
        logger.info("\n\n#### Prüfung AuftragsNr: ####")
        list_abr= df_imp.groupby(['Gpnr','Rech_Mandant'])['AbrechnungsNr'].nunique().reset_index(name="Anzahl AbrechnungsNr")
        info_abre=0
        for index, value in list_abr.iterrows():
            if value['Anzahl AbrechnungsNr'] > 1:
                logger.info(f"\n#### Achtung: Gpnr {value['Gpnr']} und Rech_Mandant {value['Rech_Mandant']} haben mehrere AbrechnungsNr ####")
                info_abre=1
                
        if info_abre==0:
            logger.info("\n#### Alle Gpnr und Rech_Mandant Kombinationen haben nur eine AbrechnungsNr ####")

        ######## Export ########
        # Alle numerischen Spalten auf 2 Nachkommastellen formatieren
        for col in ['Netto','Brutto','Gesamtbrutto','Provision']:
            df_imp[col] = df_imp[col].apply(lambda x: f"{x:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", "."))
        # Extrahieren der Downloadordners
        file_path = Path(imp)
        exp=file_path.parent / f"WM_Provisionsabrechnung_Lasernet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df_imp.to_csv(exp,index=False)
        logger.info(f"\n\n#### Prozess abgeschlossen #### \nDatei abgelegt unter: {exp}")

        # Excel Export
        if test_entry.get()==1:
            exp_excel=file_path.parent / f"WM_Provisionsabrechnung_Lasernet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df_imp.to_excel(exp_excel,index=False)
            logger.info(f"\n#### Excel-Export abgeschlossen #### \nDatei abgelegt unter: {exp_excel}")
        
    def download_Mapping(imp):
        logger.info('Download Mapping')
        Query='''
        select *
        from tb_provisionsabrechnung_mapping
        '''
        df_map=execute_sql_query(Query,database='dbm_werbemarkt')
        exp = Path(folder_path.get()) / f"Mapping_WM_Provisionsabrechnung_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df_map.to_csv(exp,sep=';',index=False)
        logger.info(f"\n#### Excel-Export abgeschlossen #### \nDatei abgelegt unter: {exp}")

    ######## Hauptfenster erstellen ########
    root = tk.Tk()  # Erstellt das Hauptfenster
    root.wm_title('WM Provisionsabrechnung - Tool')  # Titel des Fensters
    root.geometry("700x600")  # Fenstergröße: 300x200 Pixel
    # Dokumentation
    doku=tk.Button(root,text='Dokumentation',command=open_dokumentation)
    doku.grid(row=1,column=3)
    # Variablen
    file_path = tk.StringVar()
    folder_path = tk.StringVar()


    #### Importfunktion
    lable=ttk.Label(root,text='1. Importfunktion')
    lable.grid(row=2,column=2)
    # Import
    lable=ttk.Label(root,text='Importdatei wählen:')
    lable.grid(row=3,column=1)
    file_entry = ttk.Entry(root, textvariable=file_path, width=50)
    file_entry.grid(row=3,column=2)
    file_button = ttk.Button(root, text="Durchsuchen", command=browse_file)
    file_button.grid(row=3,column=3)
    # Start
    file_button = ttk.Button(root, text="Start", command=lambda: start_process(file_path.get()))
    file_button.grid(row=4,column=3)
    # Excel Button
    test_entry = tk.IntVar(value=0)
    file_button = tk.Checkbutton(root, text="Zusätzliche Excel erstellen",variable=test_entry)
    file_button.grid(row=5,column=3)


    #### Mapping downloaden
    lable=ttk.Label(root,text='2. Mapping')
    lable.grid(row=8,column=2)
    lable=ttk.Label(root,text='Exportordner wählen:')
    lable.grid(row=9,column=1)
    file_entry = ttk.Entry(root, textvariable=folder_path, width=50)
    file_entry.grid(row=9,column=2)
    file_button = ttk.Button(root, text="Durchsuchen", command=browse_folder)
    file_button.grid(row=9,column=3)
    # Download des Mappings
    file_button = ttk.Button(root, text="Mappings downladen", command=lambda: download_Mapping(folder_path.get()))
    file_button.grid(row=10,column=3)


    #### Logging
    # Frame für Log-Anzeige
    log_frame = tk.Frame(root)
    log_frame.grid(row=15, column=0,columnspan=6, padx=10, pady=10)
    # Text-Widget für Log-Ausgabe
    log_text = scrolledtext.ScrolledText(log_frame, width=85, height=20, wrap=tk.WORD)
    log_text.grid(row=16,columnspan=6, column=0)
    # Custom Logging-Handler ins Textfeld umleiten
    text_handler = TextHandler(log_text)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    text_handler.setFormatter(formatter)
    logging.getLogger().addHandler(text_handler)
    # Logger
    logger = logging.getLogger("TkinterLogger")
    logger.setLevel(logging.INFO)

    #### Ereignisschleife starten
    root.mainloop()

if __name__=="__main__":
    starte_GUI()