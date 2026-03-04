import requests
import pandas as pd
import time
from tqdm import tqdm  # Progress bar için

# DeepSeek API Ayarları
API_KEY = "sk-d9d5fb2a6cea4e2fb854cff5093a1e42"  # API keyinizi buraya girin
API_URL = "https://api.deepseek.com/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# TXT dosyasından cümleleri oku
with open("ExtractReports/1_SummaryReportsV3.txt", "r", encoding="utf-8") as file:
    sentences = [line.strip() for line in file if line.strip()]

# DataFrame oluştur
df = pd.DataFrame(sentences, columns=["sentence"])
df["label"] = ""

# Etiketleme fonksiyonu (DeepSeek uyumlu)
def classify_sentence(sentence):
    prompt = f"""
You are an expert in monetary policy communication. Classify the following sentence from the Central Bank of the Republic of Turkey (CBRT) based on its policy tone.

Sentence: "{sentence}"

Choose only one of the following labels:

- "hawkish": if the sentence signals inflationary pressure, interest rate hikes, tightening, or 
             economic risks requiring policy action.
- "dovish":  if the sentence signals easing, financial support, rate cuts, or declining inflation.
- "neutral": if the sentence is purely descriptive with no policy implications.

Return only the label as a single word: hawkish, dovish, or neutral.
"""
    
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,  # Deterministik sonuçlar için
        "max_tokens": 10
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        
        # DeepSeek API yanıt formatı
        label = response.json()["choices"][0]["message"]["content"].strip().lower()
        
        # Sadece geçerli etiketleri kabul et
        if label in ["hawkish", "dovish", "neutral"]:
            return label
        else:
            print(f"Beklenmeyen yanıt: {label} | Cümle: {sentence}")
            return "error"
            
    except Exception as e:
        print(f"Hata: {e} | Cümle: {sentence}")
        return "error"

# İşlem ve kaydetme fonksiyonu
def process_and_save(df, batch_size=50, delay=0.5):
    for idx in tqdm(range(len(df)), desc="Etiketleniyor"):
        if df.at[idx, "label"] == "":  # Sadece boş olanları işle
            df.at[idx, "label"] = classify_sentence(df.at[idx, "sentence"])
            time.sleep(delay)  # Rate limit
            
            # Batch kaydet
            if (idx + 1) % batch_size == 0:
                df.to_excel("TCMB_LABELLED_DEEPSEEK_PARTIAL.xlsx", index=False)
                print(f"\n{idx + 1} cümle işlendi. Ara kayıt yapıldı.")
    
    # Final kayıt
    df.to_excel("2_LabelwithDeepSeek.xlsx", index=False)
    print("Tüm işlem tamamlandı!")

# Çalıştır
if __name__ == "__main__":
    process_and_save(df)