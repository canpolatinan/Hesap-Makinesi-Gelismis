# 🧮 Gelişmiş Python Hesap Makinesi (v2)

Python ve `tkinter` kullanılarak geliştirilmiş; modern arayüze, tema desteğine, bilimsel işlem yeteneklerine ve güvenli ifade çözümleme mekanizmasına sahip masaüstü hesap makinesi uygulamasıdır.

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## ✨ Özellikler

* **Modern ve Şık Arayüz:** Yuvarlak köşeli özel düğmeler, dinamik yazı boyutu ayarlama ve yumuşak geçişli tasarımıyla minimalist bir görünüm.
* **Çift Tema Desteği:** Tek tuşla **Koyu (Dark)** ve **Açık (Light)** tema arasında geçiş yapabilme.
* **Basit ve Bilimsel Mod:** İhtiyaca göre tek tuşla açılıp kapanabilen bilimsel işlem paneli.
* **Güvenli Hesaplama Motoru (`ast`):** Tehlikeli olan `eval()` fonksiyonu yerine Python `ast` (Abstract Syntax Tree) modülü kullanılarak tamamen güvenli ifade değerlendirmesi.
* **Akıllı İfade İşleme:** 
  * Parantezsiz fonksiyon kullanımı (`sin30`, `√9` vb.).
  * Gerçek hayat senaryolarına uygun yüzde hesaplamaları (`50+10%` = `55`).
  * Gizli çarpma algılama (`2π`, `3(4+1)` vb.).
* **Bellek İşlemleri:** `MC`, `MR`, `M+`, `M−`, `MS` tuşlarıyla tam fonksiyonel bellek yönetimi.
* **Kalıcı İşlem Geçmişi:** Yapılan tüm işlemler geçmiş paneline kaydedilir, kapatılıp açıldığında silinmez (`.gelismis_hesap_makinesi.json` dosyasında saklanır). Geçmişteki bir sonuca çift tıklayarak tekrar işlemde kullanabilirsiniz.
* **Canlı Önizleme:** Yazım esnasında sonuçları anlık olarak görme imkanı.

---

## 🚀 Kurulum ve Çalıştırma

Bu projeyi çalıştırmak için bilgisayarınızda Python'un yüklü olması yeterlidir. Ekstra bir üçüncü taraf kütüphane (`pip install` vb.) gerektirmez, tamamen standart kütüphaneleri kullanır.

1. Projeyi bilgisayarınıza klonlayın veya indirin:
   ```bash
   git clone [https://github.com/canpolatinan/hesap-makinesi.git](https://github.com/canpolatinan/hesap-makinesi.git)
