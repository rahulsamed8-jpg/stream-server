# -----------------------------------------------------------------------------
# Gerekli kütüphaneleri içe aktarıyoruz.
# Flask: Web sunucumuzu oluşturmak için.
# Flask-SocketIO: Gerçek zamanlı (WebSocket) iletişimi yönetmek için.
# Flask-CORS: Tabletin sunucuya bağlanırken "Cross-Origin" hatasını engellemek için.
# send_from_directory: panel.html dosyasını sunmak için eklendi.
# os ve os.path: panel.html dosyasının tam yolunu bulmak için eklendi (404 Hatası Düzeltmesi)
# -----------------------------------------------------------------------------
import os
from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS

# -----------------------------------------------------------------------------
# 404 Hatası Düzeltmesi: panel.html dosyasının bulunduğu klasörü tanımla
# -----------------------------------------------------------------------------
# Bu kod, server.py dosyasının bulunduğu klasörün tam yolunu alır.
# Örn: /opt/render/project/src
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# -----------------------------------------------------------------------------
# Flask uygulamamızı başlatıyoruz.
# -----------------------------------------------------------------------------
app = Flask(__name__)
# CORS(app) ayarı, başka domainlerden (örneğin tabletinizin tarayıcısından)
# gelen isteklere izin vermemizi sağlar. Bu ÇOK ÖNEMLİDİR.
CORS(app, resources={r"/*": {"origins": "*"}})

# -----------------------------------------------------------------------------
# SocketIO'yu Flask uygulamamıza bağlıyoruz.
# -----------------------------------------------------------------------------
# cors_allowed_origins="*" ayarı da yine güvenlik için gereklidir.
socketio = SocketIO(app, cors_allowed_origins="*")

# -----------------------------------------------------------------------------
# Sunucu Durumunu Kontrol Etmek İçin Ana Sayfa
# Tarayıcıdan VPS'inizin IP adresini (http://VPS_IP_ADRESINIZ:5000) açtığınızda
# bu mesajı görüyorsanız, sunucu çalışıyor demektir.
# -----------------------------------------------------------------------------
@app.route('/')
def index():
    return "Python Sinyal Sunucusu Aktif! Bağlantı bekleniyor..."

# -----------------------------------------------------------------------------
# Panel Arayüzünü Sunmak İçin EKLENEN KISIM
# http://.../panel adresine girildiğinde panel.html dosyasını gönderir.
# -----------------------------------------------------------------------------
@app.route('/panel')
def send_panel():
    # 404 Hatası Düzeltmesi: Artık '.' yerine BASE_DIR (tam yol) kullanıyoruz.
    # Bu, panel.html dosyasını %100 bulmasını sağlar.
    return send_from_directory(BASE_DIR, 'panel.html')

# -----------------------------------------------------------------------------
# İLETİŞİM (SİNYALLEŞME) OLAYLARI
# -----------------------------------------------------------------------------

# Sabit bir "oda" ismi belirliyoruz. 
# Telefon ve tabletin aynı odada buluşmasını sağlayacağız.
# Daha gelişmiş bir sistemde bu oda ismi dinamik (örn: kullanıcı ID'si) olabilir.
STREAM_ROOM = 'yayindayim'

# 1. BİR İSTEMCİ (TELEFON VEYA TABLET) BAĞLANDIĞINDA
@socketio.on('connect')
def handle_connect():
    # VPS'in terminal ekranında bu mesajı göreceğiz.
    print(f"BİR İSTEMCİ BAĞLANDI. SID: {request.sid}")
    # Bağlanan her istemciyi otomatik olarak yayın odamıza alıyoruz.
    join_room(STREAM_ROOM)
    print(f"İstemci {request.sid}, '{STREAM_ROOM}' odasına katıldı.")

# 2. BİR İSTEMCİ BAĞLANTISI KESİLDİĞİNDE
@socketio.on('disconnect')
def handle_disconnect():
    print(f"BİR İSTEMCİ AYRILDI. SID: {request.sid}")
    # İstemciyi odadan çıkarıyoruz.
    leave_room(STREAM_ROOM)
    print(f"İstemci {request.sid}, '{STREAM_ROOM}' odasından ayrıldı.")
    
    # Gelişmiş: Eğer ayrılan kişi yayıncı (telefon) ise, 
    # izleyiciye (tablete) 'yayin_bitti' mesajı gönderebiliriz.
    emit('yayin_bitti', {'message': 'Yayıncı bağlantıyı sonlandırdı.'}, to=STREAM_ROOM, include_self=False)

# 3. TABLETTEN "YAYINI BAŞLAT" KOMUTU GELDİĞİNDE
@socketio.on('izleyici_baslat_komutu')
def handle_start_command(data):
    print(f"İzleyiciden (tablet) 'başlat' komutu alındı: {data}")
    # Bu komutu odadaki DİĞER kişiye (yani telefona) iletiyoruz.
    # include_self=False: Komutu gönderen tablete geri gönderme.
    emit('server_yayini_iste', {'command': 'Lütfen yayını başlat.'}, to=STREAM_ROOM, include_self=False)
    print("Komut telefona iletildi (telefondan yanıt bekleniyor).")

# 4. WEBRTC SİNYAL İLETİŞİMİ (EN ÖNEMLİ KISIM)
# WebRTC (ekran paylaşımı) bağlantısı kurulurken, telefon ve tablet
# birbirlerine "offer" (teklif), "answer" (cevap) ve "ice candidate" (adres bilgisi)
# gibi sinyal mesajları gönderir. Bu fonksiyon, bu mesajlara aracılık eder.
@socketio.on('signal')
def handle_signal(data):
    # Birinden (örn: telefon) gelen sinyali, odadaki diğer kişiye (örn: tablet)
    # OLDUĞU GİBİ iletiyoruz. Sunucu bu 'data'nın içeriğini bilmek zorunda değildir.
    print(f"Sinyal alınıyor ve iletiliyor: {data.get('type')}")
    emit('signal', data, to=STREAM_ROOM, include_self=False)


# -----------------------------------------------------------------------------
# Sunucuyu Başlatma Bloğu
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    print("Sinyal sunucusu başlatılıyor...")
    
    # Render.com'un istediği "allow_unsafe_werkzeug=True" eklendi.
    # Bu, "RuntimeError" hatasını çözecek.
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=10000, 
        allow_unsafe_werkzeug=True
    )

