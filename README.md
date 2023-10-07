# BOE/BORME Downloader

Simple tool to download all the BOE or BORME documents from a given date.

## Installation

Install all the required third-parties python modules through pip:

```bash
python3 -m pip install -r requirements.txt
```

## Usage

Here you can find some examples on how to call and use the tool through the different expected arguments.

Download BOE documents from 2023/10/05 and store it in ./downdocs directory:

```bash
python3 boe_borme_downloader.py --outdir ./downdocs --type boe --date 20231005
```

Download BORME documents from 2023/10/06 and store it in ./downdocs directory:

```bash
python3 boe_borme_downloader.py --outdir ./downdocs --type borme --date 20231006
```
