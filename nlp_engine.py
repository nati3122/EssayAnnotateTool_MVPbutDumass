import ollama
import json

class NLPEngine:
    def __init__(self, model_name="phi3"):
        self.model_name = model_name

    def check_essay(self, full_text):
        prompt = f"""
        List the English grammar or spelling errors in the following text.
        Return the result as a JSON array of objects. 
        Each object MUST have:
        1. "original": the incorrect phrase from the text.
        2. "type": either "spelling", "grammar", or "semantic".

        Text to analyze:
        "{full_text[:1200]}"
        """
        
        try:
            print(f"--- 正在與本地模型 {self.model_name} 通訊 (JSON Mode) ---")
            response = ollama.chat(
                model=self.model_name,
                format='json',
                messages=[{'role': 'user', 'content': prompt}]
            )
            content = response['message']['content']
            print(f"DEBUG AI 原始輸出: {content}")
            
            data = json.loads(content)
            # normalize different response structures into a list
            if isinstance(data, list):
                raw_list = data
            elif isinstance(data, dict):
                raw_list = []
                for v in data.values():
                    if isinstance(v, list):
                        raw_list = v
                        break
                if not raw_list:
                    raw_list = [data]
            else:
                raw_list = []

            cleaned_errors = []
            for item in raw_list:
                if not isinstance(item, dict):
                    continue
                orig = item.get('original') or item.get('error') or item.get('message')
                if not orig:
                    continue
                tval = item.get('type', 'grammar')
                # handle type lists or other weird formats
                if isinstance(tval, list) and tval:
                    tval = tval[0]
                tstr = str(tval).lower()
                if '/' in tstr or ',' in tstr:
                    import re
                    tstr = re.split('[/,]', tstr)[0]
                if tstr not in ('spelling', 'grammar', 'semantic'):
                    tstr = 'grammar'
                cleaned_errors.append({
                    "original": str(orig),
                    "type": tstr
                })
            return cleaned_errors
        except Exception as e:
            print(f"NLP 解析出錯: {e}")
            return []