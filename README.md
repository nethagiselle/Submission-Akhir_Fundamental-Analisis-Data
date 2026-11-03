# Submission-Akhir_Fundamental-Analisis-Data
## Struktur Folder
```
submission/
├── dashboard/
│   ├── dashboard.py
│   └── main_data.csv
├── data/
│   └── PRSA_Data_*.csv (12 berkas)
├── notebook.ipynb
├── README.md
└── requirements.txt
```

## Setup Environment - Anaconda

```
conda create --name main-ds python=3.9
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal

```
cd path/ke/folder-submission
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Untuk macOS atau Linux, ganti perintah aktivasi dengan `source venv/bin/activate`.

Jika PowerShell menolak menjalankan script aktivasi, jalankan perintah ini terlebih dahulu:

```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Run Streamlit App

```
streamlit run dashboard/dashboard.py
```

Dashboard akan terbuka di `http://localhost:8501`.
