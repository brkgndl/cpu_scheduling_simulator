# CPU Zamanlama Simülatörü

Bu proje işletim sistemleri dersi kapsamında geliştirdiğim CPU zamanlama algoritmaları için bir simülatördür.

Uygulama, farklı senaryoları test etmek için **FCFS, SJF, Round Robin ve diğer** temel algoritmaları kullanır ve performans metriklerini karşılaştırır.

##Bu projeyi aşağıdaki Streamlit uygulamasıyla interaktif olarak incelemeniz tavsiye edilir.Orada denemeler yaptıktan sonra bu Readme dosyasının en altında bazı yorum ve çıkarımlara ulaşabilirsiniz.
Projeyi hiçbir kurulum yapmadan tarayıcınız üzerinden test edebilirsiniz:
👉 **[UYGULAMAYA GİT !](https://cpu-zamanlama-simulator.streamlit.app/)**
---

* **6 Farklı Algoritma:**
    * FCFS (First Come First Served)
    * SJF (Shortest Job First) - Non-Preemptive
    * SJF (Shortest Job First) - Preemptive (SRTF)
    * Round Robin (RR)
    * Priority Scheduling - Non-Preemptive
    * Priority Scheduling - Preemptive
* **Eş Zamanlı Hesaplama:** Python `threading` kütüphanesi kullanılarak tüm algoritmalar aynı anda, birbirini bloklamadan çalıştırılır. (BONUS)
* **Görselleştirme:**
    * **Gantt Şemaları:** Süreçlerin zaman çizelgesi üzerinde ne zaman çalıştığını gösteren interaktif grafikler.
    * **Performans Grafikleri:** Bekleme süresi ve CPU verimliliği karşılaştırmaları.
* **Esnek Veri Girişi:**
    * Kendi `.txt` veya `.csv` processes dosyanızı yükleyebilirsiniz.
    * Hazır senaryoları (`case1.txt`, `case2.txt`) tek tıkla kullanabilirsiniz.
* **Raporlama:** Her algoritma için detaylı metin raporları (ödevde istenen tüm maddeler) oluşturulur ve `.txt` formatında indirilebilir.

## 📖 Kullanım Kılavuzu

1.  Uygulama açıldığında sol taraftaki **Ayarlar** menüsünü kullanın.
2.  **Veri Kaynağı Seçin:**
    * *Dosya Yükle:* Kendi veri setinizi yükleyin.
    * *Hazır Örnek Kullan:* `case1` veya `case2` senaryolarından birini seçin.
3.  **Parametreleri Ayarlayın:**
    * *Round Robin Quantum:* RR algoritması için zaman dilimi (Varsayılan: 10).
    * *Context Switch:* Bağlam değiştirme maliyeti (Varsayılan: 0.001 ms).
4.  **"Simülasyonu Başlat"** butonuna tıklayın.
5.  Sonuçlar hesaplandıktan sonra sekmeler arasında gezinerek **Özet Tabloyu**, **Grafikleri** ve **Detaylı Raporları** inceleyebilirsiniz.

---

## 📂 Dosya Yapısı

* `main.py`: Ana uygulama ve algoritma kodları.
* `case1.txt`: Düşük işlem süreli 200 süreci içeren test verisi.
* `case2.txt`: Yüksek işlem süreli 100 süreci içeren test verisi.
* `requirements.txt`: Gerekli Python kütüphaneleri listesi.

---

## 📊 Deneysel Sonuçlar ve Algoritma Analizleri

Proje kapsamında `case1.txt` (200 süreç, kısa burst süreli) ve `case2.txt` (100 süreç, uzun burst süreli) veri setleri üzerinde yapılan testlerin çıkarımları aşağıdadır.

### 1. Bekleme Süresi (Waiting Time) Analizi
* **En İyi Performans:** Her iki senaryoda da **Preemptive SJF** ve **Non-Preemptive SJF** algoritmaları en düşük ortalama bekleme süresini vermiştir. Bunun nedeni, SJF'nin "kısa işi öne al" mantığıyla kuyrukta bekleyen işlem sayısını en düşük seviyede tutmasıdır.
* **En Kötü Performans:** **FCFS (First Come First Served)** algoritması, özellikle `case2.txt` gibi uzun burst sürelerine sahip süreçlerin olduğu durumlarda **"Konvoy Etkisi"** yaratmış ve ortalama bekleme süresini ciddi oranda artırmıştır.

### 2. İşlemci Verimliliği ve Context Switch
* **Round Robin (RR):** RR algoritması (Quantum=10), sistemin tepki süresini iyileştirse de, sık sık işlemciyi başka sürece geçirdiği için **Context Switch** sayısına sahiptir. Bu durum, simülasyonda işlemci verimliliğini bir miktar düşüren bir yük oluşturmuştur.
* **Preemptive vs Non-Preemptive:** Preemptive (Kesintili) algoritmalar (Priority Preemptive ve SJF Preemptive), yeni ve daha öncelikli bir iş geldiğinde mevcut işi kestiği için Non-Preemptive yöntemlere göre daha fazla context switching maliyeti oluşturmuştur. Ancak dinamik sistemlerde acil işlerin tamamlanması için bu maliyet kabul edilebilirdir.

### 3. Throughput
* **T=50 ve T=100 Anları:** Simülasyonun ilk aşamalarında (T=50 gibi), **SJF** algoritmaları diğerlerine göre daha fazla sayıda süreç tamamlamıştır (Bunları Streamlit'ten çok daha keyifli şekilde kendiniz gözlemleyebilirsiniz.). Bunun sebebi, kısa sürecek işleri hemen bitirip sistemden çıkarmasıdır.
* **FCFS Karşılaştırması:** FCFS algoritmasında, eğer başlangıçta uzun süren bir işlem varsa, T=50 anında tamamlanan iş sayısı 0 veya 1'de kalabilmektedir. Bu durum, kısa işlerin uzun işleri beklemesi sorununu (Starvation) net bir şekilde göstermiştir.

### Genel Değerlendirme
Yapılan testler sonucunda;
1.  **Maksimum Verimlilik İçin:** İşlemci süresi önceden biliniyorsa **SJF (Shortest Job First)** en iyi seçimdir.
2.  **Daha adaletli ve Etkileşimli durumlar için:** Kullanıcı etkileşimli sistemlerde **Round Robin**, her işleme eşit hak tanıdığı için tercih edilmelidir.
3.  **Önem Derecesi İçin:** Kritik görevlerin olduğu senaryolarda **Priority Scheduling** zorunludur, ancak düşük öncelikli işlemlerin starvation çekme riski gözlemlenmiştir.

Bu proje tüm bu algoritmaları interaktif bir ortamda test edebilme ve birbirleriyle karşılaştırarak bu CPU scheduling algoritmalarının güçlü ve zayıf yönlerini analiz etme yeteneğimi güçlendirmiş, halihazırdaki hakimiyetimi oldukça güçlendirmiştir :) 
