import easyocr
import numpy as np

class OCREngine:
    def __init__(self, use_gpu=False):
        print("正在初始化 EasyOCR 引擎...")
        self.reader = easyocr.Reader(['en'], gpu=use_gpu)

    def get_ocr_result(self, pixmap):
        img = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, 3)
        
        # 調優參數說明：
        # text_threshold: 降低文字偵測門檻（預設 0.7），讓模糊的手寫字更容易被發現
        # low_text: 捕捉更細微的筆跡
        # mag_ratio: 放大比例，手寫字較小時增加此值可提高準確率
        result = self.reader.readtext(
            img, 
            detail=1,
            text_threshold=0.5, 
            low_text=0.3,
            mag_ratio=2.0 
        )
        
        processed_data = []
        for (bbox, text, prob) in result:
            processed_data.append({
                "text": text,
                "box": bbox,
                "confidence": prob
            })
        return processed_data