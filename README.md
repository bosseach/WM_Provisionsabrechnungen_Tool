# WM Provisionsabrechnungen Tool

Tool für das Erstellen der Datensätzen der Provisionsabrechnung des Werbemarktes für Lasernet

## Prozess
1. Download der Rohdaten aus Dialog One
2. Ausführen des Tools. Dieses bearbeitet die Daten und fügt Informationen aus der DOA Datenbank "ATLAS" hinzu
3. Ablegen der Daten für lasernet

## Struktur 

```text
WM_Provisionsabrechnungen_Tool/
|-- GUI.py
|-- requirements.txt
|-- Readme.md
|-- CHANGELOG.md
```

## Installation

Empfohlen wird die Verwendung einer virtuellen Umgebung:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

## Erstellen einer .exe
```bash
pyinstaller --clean GUI.spec
```

## Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in `CHANGELOG.md` dokumentiert.
