import fitz
import re
import difflib
from ocr_engine import OCREngine 
from nlp_engine import NLPEngine
from annotator import Annotator

def get_similarity(s1, s2):
    return difflib.SequenceMatcher(None, s1, s2).ratio()

def process_entire_document(input_pdf, output_pdf):
    # 利用 RTX 2080 Ti 啟用 GPU 加速
    ocr_tool = OCREngine(use_gpu=True) 
    nlp_tool = NLPEngine(model_name="phi3") 
    annot_tool = Annotator() 
    
    zoom = 2.0
    mat = fitz.Matrix(zoom, zoom)
    doc = fitz.open(input_pdf)
    all_pages_data = []
    full_text = ""

    print(f"📄 開始處理: {input_pdf}...")

    # 1. OCR 掃描 (GPU 加速)
    for page_num in range(len(doc)):
        pix = doc[page_num].get_pixmap(matrix=mat)
        results = ocr_tool.get_ocr_result(pix)
        all_pages_data.append({"page_num": page_num, "words": results})
        full_text += " ".join([w['text'] for w in results]) + " "

    # 2. AI 分析
    errors = nlp_tool.check_essay(full_text) 
    print(f"📝 AI 發現 {len(errors)} 個潛在錯誤")

    # 3. 座標分群與匹配
    grouped_markers = {}
    for err in errors:
        orig = err.get('original', '').lower().strip()
        if len(orig) < 2: continue
        
        target_kws = re.findall(r'\w+', orig) # 將錯誤短語拆開匹配
        
        for p_data in all_pages_data:
            for w_item in p_data['words']:
                ocr_c = re.sub(r'[^\w]', '', w_item['text'].lower())
                if not ocr_c: continue

                # 多重匹配邏輯：精確相同、相似度高 (>80%)、包含關係
                if any(kw == ocr_c or get_similarity(kw, ocr_c) > 0.8 or kw in ocr_c for kw in target_kws if len(kw)>1):
                    box = w_item['box']
                    # 建立座標唯一 Key (元組格式)
                    key = (p_data['page_num'], box[0][0], box[0][1], box[2][0], box[2][1])
                    
                    if key not in grouped_markers:
                        grouped_markers[key] = []
                    if err['type'] not in grouped_markers[key]:
                        grouped_markers[key].append(err['type'])

    # 4. 繪製並存檔（無論是否有標註都會產生輸出）
    if not grouped_markers:
        print("⚠️ 未發現可匹配的標註區域。將複製原始文件為輸出。")
    # mark_errors 現在能接受空的 dict/list 並且會儲存原始 PDF
    annot_tool.mark_errors(input_pdf, output_pdf, grouped_markers, zoom_factor=zoom)

if __name__ == "__main__":
    process_entire_document("test34.pdf", "full_report.pdf")