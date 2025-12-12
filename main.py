import streamlit as st
import pandas as pd
import plotly.express as px
import csv
import threading
import copy
import os
from io import StringIO

# STREAMLIT AYARLARI
st.set_page_config(page_title="CPU Zamanlama Simülatörü", layout="wide", page_icon="💻")

st.title("💻 CPU Zamanlama Simülatörü")
st.markdown("""
Bu uygulama **FCFS, SJF, Round Robin ve diğer CPU zamanlama** algoritmalarını simüle eder.
Sol menüden kendi dosyanızı yükleyebilir veya **hazır test senaryolarını (Case 1 & 2)** kullanabilirsiniz.
""")

# default ayarlarımız
QUANTUM_DEFAULT = 10
CONTEXT_SWITCH_DEFAULT = 0.001
ONCELIKLER = {"high": 1, "normal": 2, "low": 3}

# Bazı gerekli fonksiyonlar

def dosya_oku_veya_yukle(dosya_kaynagi):
    islemler = []
    try:
        if isinstance(dosya_kaynagi, str):
            if not os.path.exists(dosya_kaynagi):
                st.error(f"⚠️ Hata: '{dosya_kaynagi}' dosyası bulunamadı!")
                return []
            f = open(dosya_kaynagi, 'r')
            
        # 2.Kullanıcı bilgisayarından yüklediyse (UploadedFile objesi gelir)
        else:
            stringio = StringIO(dosya_kaynagi.getvalue().decode("utf-8"))
            f = stringio

        okuyucu = csv.reader(f)
        baslik = next(okuyucu, None)
        
        for satir in okuyucu:
            if len(satir) < 4: continue
            islem = {
                'id': satir[0],
                'varis': int(satir[1]),
                'patlama': int(satir[2]),
                'oncelik': ONCELIKLER.get(satir[3].strip().lower(), 3),
                'kalan_sure': int(satir[2]),
                'baslama': -1, 'bitis': 0, 'bekleme': 0, 'donus': 0
            }
            islemler.append(islem)
            
        if isinstance(dosya_kaynagi, str):
            f.close()     
    except Exception as e:
        st.error(f"Dosya okuma hatası: {e}")
        return []
    return islemler

def rapor_olustur(algoritma_adi, zaman_cizelgesi, islemler, cs_sayisi, toplam_sure, context_switch_time, sonuc_listesi, lock):
    # Hesaplamalar
    tamamlananlar = [p for p in islemler if p['bitis'] > 0]
    tamamlananlar.sort(key=lambda x: x['id']) 
    
    toplam_wt, toplam_tat = 0, 0
    max_wt, max_tat = 0, 0
    toplam_is_yuku = 0
    
    for p in tamamlananlar:
        p['donus'] = p['bitis'] - p['varis']
        p['bekleme'] = p['donus'] - p['patlama']
        toplam_wt += p['bekleme']
        toplam_tat += p['donus']
        toplam_is_yuku += p['patlama']
        if p['bekleme'] > max_wt: max_wt = p['bekleme']
        if p['donus'] > max_tat: max_tat = p['donus']
        
    ort_wt = toplam_wt / len(tamamlananlar) if tamamlananlar else 0
    ort_tat = toplam_tat / len(tamamlananlar) if tamamlananlar else 0
    
    throughput_sonuc = {t: sum(1 for p in tamamlananlar if p['bitis'] <= t) for t in [50, 100, 150, 200]}

    verimlilik = 0
    if toplam_sure > 0:
        payda = toplam_sure + (cs_sayisi * context_switch_time)
        verimlilik = (toplam_is_yuku / payda) * 100

    # Metin Raporu
    cikti_metni = f"Algorithm Result: {algoritma_adi}\n"
    cikti_metni += "-" * 30 + "\n"
    cikti_metni += "a) Zaman Tablosu (Timeline):\n"
    for bas, bit, pid in zaman_cizelgesi:
        cikti_metni += f"[ {bas} ] - - {pid} - - [ {bit} ]\n"
    
    cikti_metni += f"\nb) Bekleme Sureleri:\n   Maksimum: {max_wt}\n   Ortalama: {ort_wt:.2f}\n"
    cikti_metni += f"c) Tamamlanma Sureleri:\n   Maksimum: {max_tat}\n   Ortalama: {ort_tat:.2f}\n"
    cikti_metni += "d) Is Tamamlama Sayisi (Throughput):\n"
    for t, val in throughput_sonuc.items():
        cikti_metni += f"   T={t}: {val}\n"
    cikti_metni += f"e) CPU Verimliligi: %{verimlilik:.4f}\n"
    cikti_metni += f"f) Baglam Degistirme: {cs_sayisi}\n"

    # Veri Paketi
    dosya_adi = f"{algoritma_adi.replace(' ', '_')}_Output.txt"
    veri_paketi = {
        "Algoritma": algoritma_adi,
        "Ort_Bekleme": ort_wt,
        "Ort_Turnaround": ort_tat,
        "Verimlilik": verimlilik,
        "Context_Switch": cs_sayisi,
        "Throughput_200": throughput_sonuc[200],
        "Cizelge": zaman_cizelgesi,
        "Rapor_Metni": cikti_metni,
        "Dosya_Adi": dosya_adi
    }
    
    # Thread bozmadan kayıt yapalım
    with lock:
        sonuc_listesi.append(veri_paketi)

# Zamanlama Algoritmalarımız

def fcfs_calistir(islemler, params, sonuc_listesi, lock):
    liste = sorted(islemler, key=lambda x: x['varis'])
    zaman, cs = 0, 0
    cizelge, son_id = [], None
    for p in liste:
        if zaman < p['varis']:
            cizelge.append((zaman, p['varis'], "IDLE"))
            zaman = p['varis']
        if son_id != p['id']:
            cs += 1
            son_id = p['id']
        bas = zaman
        zaman += p['patlama']
        p['bitis'] = zaman
        cizelge.append((bas, zaman, p['id']))
    if cs > 0: cs -= 1
    rapor_olustur("FCFS", cizelge, liste, cs, zaman, params['cs_time'], sonuc_listesi, lock)

def sjf_non_pre_calistir(islemler, params, sonuc_listesi, lock):
    zaman, tamamlanan, cs = 0, 0, 0
    cizelge, son_id = [], None
    kalanlar = islemler[:]
    while tamamlanan < len(islemler):
        hazir = [p for p in kalanlar if p['varis'] <= zaman]
        if not hazir:
            kalanlar.sort(key=lambda x: x['varis'])
            zaman = kalanlar[0]['varis']
            if cizelge: cizelge.append((cizelge[-1][1], zaman, "IDLE"))
            continue
        secilen = min(hazir, key=lambda x: x['patlama'])
        if son_id != secilen['id']:
            cs += 1
            son_id = secilen['id']
        bas = zaman
        zaman += secilen['patlama']
        secilen['bitis'] = zaman
        cizelge.append((bas, zaman, secilen['id']))
        kalanlar.remove(secilen)
        tamamlanan += 1
    if cs > 0: cs -= 1
    rapor_olustur("SJF Non-Preemptive", cizelge, islemler, cs, zaman, params['cs_time'], sonuc_listesi, lock)

def sjf_pre_calistir(islemler, params, sonuc_listesi, lock):
    zaman, tamamlanan, cs = 0, 0, 0
    cizelge, aktif = [], None
    segment_basi = 0
    n = len(islemler)
    while tamamlanan < n:
        hazir = [p for p in islemler if p['varis'] <= zaman and p['kalan_sure'] > 0]
        if not hazir:
            if aktif:
                cizelge.append((segment_basi, zaman, aktif['id']))
                aktif = None
            zaman += 1
            continue
        secilen = min(hazir, key=lambda x: x['kalan_sure'])
        if secilen != aktif:
            if aktif: cizelge.append((segment_basi, zaman, aktif['id']))
            elif zaman > 0 and (not cizelge or cizelge[-1][1] != zaman):
                 cizelge.append((cizelge[-1][1] if cizelge else 0, zaman, "IDLE"))
            cs += 1
            aktif = secilen
            segment_basi = zaman
        secilen['kalan_sure'] -= 1
        zaman += 1
        if secilen['kalan_sure'] == 0:
            secilen['bitis'] = zaman
            tamamlanan += 1
            cizelge.append((segment_basi, zaman, secilen['id']))
            aktif = None
    if cs > 0: cs -= 1
    rapor_olustur("SJF Preemptive", cizelge, islemler, cs, zaman, params['cs_time'], sonuc_listesi, lock)

def rr_calistir(islemler, params, sonuc_listesi, lock):
    kuyruk, cizelge = [], []
    zaman, cs, tamamlanan = 0, 0, 0
    sirali = sorted(islemler, key=lambda x: x['varis'])
    eklendi = [False] * len(sirali)
    aktif = None
    quantum = params['quantum']
    while tamamlanan < len(islemler):
        for i, p in enumerate(sirali):
            if not eklendi[i] and p['varis'] <= zaman:
                kuyruk.append(p)
                eklendi[i] = True
        if not kuyruk:
            cizelge.append((zaman, zaman+1, "IDLE"))
            zaman += 1
            continue
        secilen = kuyruk.pop(0)
        if aktif != secilen:
            cs += 1
            aktif = secilen
        bas = zaman
        calisma = min(secilen['kalan_sure'], quantum)
        zaman += calisma
        secilen['kalan_sure'] -= calisma
        cizelge.append((bas, zaman, secilen['id']))
        for i, p in enumerate(sirali):
            if not eklendi[i] and p['varis'] <= zaman:
                kuyruk.append(p)
                eklendi[i] = True
        if secilen['kalan_sure'] > 0: kuyruk.append(secilen)
        else:
            secilen['bitis'] = zaman
            tamamlanan += 1
    if cs > 0: cs -= 1
    rapor_olustur("Round Robin", cizelge, islemler, cs, zaman, params['cs_time'], sonuc_listesi, lock)

def prio_non_pre_calistir(islemler, params, sonuc_listesi, lock):
    zaman, tamamlanan, cs = 0, 0, 0
    cizelge, son_id = [], None
    kalanlar = islemler[:]
    while tamamlanan < len(islemler):
        hazir = [p for p in kalanlar if p['varis'] <= zaman]
        if not hazir:
            kalanlar.sort(key=lambda x: x['varis'])
            zaman = kalanlar[0]['varis']
            if cizelge: cizelge.append((cizelge[-1][1], zaman, "IDLE"))
            continue
        secilen = min(hazir, key=lambda x: x['oncelik'])
        if son_id != secilen['id']:
            cs += 1
            son_id = secilen['id']
        bas = zaman
        zaman += secilen['patlama']
        secilen['bitis'] = zaman
        cizelge.append((bas, zaman, secilen['id']))
        kalanlar.remove(secilen)
        tamamlanan += 1
    if cs > 0: cs -= 1
    rapor_olustur("Priority Non-Preemptive", cizelge, islemler, cs, zaman, params['cs_time'], sonuc_listesi, lock)

def prio_pre_calistir(islemler, params, sonuc_listesi, lock):
    zaman, tamamlanan, cs = 0, 0, 0
    cizelge, aktif = [], None
    segment_basi = 0
    n = len(islemler)
    while tamamlanan < n:
        hazir = [p for p in islemler if p['varis'] <= zaman and p['kalan_sure'] > 0]
        if not hazir:
            if aktif:
                cizelge.append((segment_basi, zaman, aktif['id']))
                aktif = None
            zaman += 1
            continue
        secilen = min(hazir, key=lambda x: x['oncelik'])
        if secilen != aktif:
            if aktif: cizelge.append((segment_basi, zaman, aktif['id']))
            elif zaman > 0 and (not cizelge or cizelge[-1][1] != zaman):
                 cizelge.append((cizelge[-1][1] if cizelge else 0, zaman, "IDLE"))
            cs += 1
            aktif = secilen
            segment_basi = zaman
        secilen['kalan_sure'] -= 1
        zaman += 1
        if secilen['kalan_sure'] == 0:
            secilen['bitis'] = zaman
            tamamlanan += 1
            cizelge.append((segment_basi, zaman, secilen['id']))
            aktif = None
    if cs > 0: cs -= 1
    rapor_olustur("Priority Preemptive", cizelge, islemler, cs, zaman, params['cs_time'], sonuc_listesi, lock)

def thread_runner(func, veri, params, sonuc_listesi, lock):
    kopya_veri = copy.deepcopy(veri)
    func(kopya_veri, params, sonuc_listesi, lock)

# İnteraktif app imiz

with st.sidebar:
    st.header("⚙️ Ayarlar")
    
    # KULLANICI SEÇİMİ: Dosya Yükle veya Hazır Seç
    veri_kaynagi = st.radio(
        "Veri Kaynağı Seçin:",
        ("Dosya Yükle", "Hazır Örnek Kullan (Case 1/2)")
    )

    secilen_dosya = None

    if veri_kaynagi == "Dosya Yükle":
        secilen_dosya = st.file_uploader("Bir süreç dosyası ekleyin (.txt/.csv)", type=["txt", "csv"])
    else:
        # Hazır dosyalar listesi
        ornek_secim = st.selectbox(
            "Hazır dosya seçin:",
            ("case1.txt", "case2.txt")
        )
        secilen_dosya = ornek_secim # Bu bir string (dosya yolu) olacak

    st.divider()
    
    st.subheader("Parametreler")
    quantum_val = st.slider("Round Robin Quantum", 1, 50, QUANTUM_DEFAULT)
    cs_val = st.number_input("Context Switch Süresi", value=CONTEXT_SWITCH_DEFAULT, format="%.4f")
    
    baslat_btn = st.button("🚀 Simülasyonu Başlat", type="primary")

if baslat_btn:
    ham_veri = []
    
    # 1. DOSYAYI AL (Seçime göre)
    if secilen_dosya is None:
        st.warning("⚠️ Lütfen bir dosya yükleyin veya hazır örneklerden birini seçin.")
    else:
        # Seçilen dosya (yol string'i veya uploaded object) fonksiyona gider
        ham_veri = dosya_oku_veya_yukle(secilen_dosya)

    if ham_veri:
        # 2. HESAPLA
        yerel_sonuclar = []
        thread_lock = threading.Lock()
        
        threads = []
        parametreler = {'quantum': quantum_val, 'cs_time': cs_val}
        algoritmalar = [fcfs_calistir, sjf_non_pre_calistir, sjf_pre_calistir, rr_calistir, prio_non_pre_calistir, prio_pre_calistir]
        
        with st.spinner('Algoritmalar hesaplanıyor...'):
            for func in algoritmalar:
                t = threading.Thread(target=thread_runner, args=(func, ham_veri, parametreler, yerel_sonuclar, thread_lock))
                threads.append(t)
                t.start()
            for t in threads: t.join()
        
        st.session_state['sonuclar'] = yerel_sonuclar
        st.success("Analiz başarıyla tamamlandı!")

# --- SONUÇLARI GÖSTER ---
if 'sonuclar' in st.session_state and st.session_state['sonuclar']:
    df = pd.DataFrame(st.session_state['sonuclar'])
    
    # 1. ÖZET TABLO
    st.subheader("📊 Özet Karşılaştırma Tablosu")
    st.dataframe(
        df[["Algoritma", "Ort_Bekleme", "Ort_Turnaround", "Verimlilik", "Context_Switch"]]
        .style.format({
            "Ort_Bekleme": "{:.2f}",
            "Ort_Turnaround": "{:.2f}",
            "Verimlilik": "{:.2f}",
            "Context_Switch": "{:.0f}"
        })
    )
    
    # 2. İNDİRME BUTONLARI
    st.subheader("📥 Rapor Dosyalarını İndir (.txt)")
    cols = st.columns(len(df))
    for i, res in df.iterrows():
        with cols[i % len(cols)]:
            st.download_button(
                label=f"⬇️ {res['Algoritma']}",
                data=res['Rapor_Metni'],
                file_name=res['Dosya_Adi'],
                mime="text/plain"
            )

    st.divider()

    # 3. DETAYLI RAPORLAR
    st.header("📄 Detaylı Analiz & Grafikler")
    tabs = st.tabs(df["Algoritma"].tolist())
    
    for i, tab in enumerate(tabs):
        sonuc = df.iloc[i]
        with tab:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.subheader(f"📜 {sonuc['Algoritma']} Raporu (Lütfen zaman tablosundan sonraki kısmı da inceleyin!)")
                st.code(sonuc['Rapor_Metni'], language="text")
            with col2:
                st.subheader("⏱️ Görsel Çizelge")
                gantt_data = [dict(Task=pid, Start=bas, Finish=bit, Resource=pid) for bas, bit, pid in sonuc["Cizelge"]]
                if gantt_data:
                    df_g = pd.DataFrame(gantt_data)
                    st.plotly_chart(px.bar(df_g, x=df_g.Finish-df_g.Start, y="Task", base="Start", orientation='h', color="Resource", title=f"{sonuc['Algoritma']}"), use_container_width=True)