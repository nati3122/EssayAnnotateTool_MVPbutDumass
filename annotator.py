import fitz

class Annotator:
    @staticmethod
    def mark_errors(input_pdf, output_pdf, error_list, zoom_factor=2.0):
        """簡易標註器。支援兩種錯誤格式：
            * 列表形式: [{"page": int, "box": [(x0,y0),(x1,y1)], "type": "spelling"}, ...]
            * 群組字典: {(page,x0,y0,x1,y1): ["spelling","grammar"], ...}
        """
        doc = fitz.open(input_pdf)
        
        # 定義顏色與標籤
        COLOR_MAP = {
            "spelling": (1, 0.3, 0.3),  # 淺紅色
            "grammar": (1, 0.8, 0),    # 橘黃色
            "semantic": (0.3, 0.3, 1), # 淺藍色
        }
        
        # 初始化錯誤統計字典
        error_counts = {key: 0 for key in COLOR_MAP.keys()}
        
        # 若傳入的是 dict 則轉換為 list
        if isinstance(error_list, dict):
            converted = []
            for coord, types in error_list.items():
                # coord 格式: (page, x0, y0, x1, y1)
                page_num, x0, y0, x1, y1 = coord
                for t in types:
                    converted.append({
                        "page": page_num,
                        "box": [(x0, y0), (x1, y1)],
                        "type": t
                    })
            error_list = converted
        
        # 1. 執行標註
        for err in error_list:
            page = doc[err["page"]]
            box = err["box"]
            # 支援 2 點 (左上、右下) 或任意多點的列表
            if len(box) >= 2:
                x0, y0 = box[0]
                x1, y1 = box[-1]
            else:
                # 異常資料，跳過
                continue
            rect = fitz.Rect(x0/zoom_factor, y0/zoom_factor, 
                             x1/zoom_factor, y1/zoom_factor)
            
            err_type = err.get("type", "grammar").lower()
            if err_type not in COLOR_MAP:
                err_type = "grammar" # 防呆機制
            
            # 增加統計計數
            error_counts[err_type] += 1
            
            color = COLOR_MAP.get(err_type)
            
            # 替換標註方式：外框 + 類型文字
            shape = page.new_shape()
            shape.draw_rect(rect)
            shape.finish(fill=None, color=color, width=1.0)
            shape.commit()
            # 標籤在方框上方顯示
            label = err_type.capitalize()
            text_pos = (rect.x0, rect.y0 - 10)
            page.insert_text(text_pos, label, fontsize=8, color=color)

        # 2. 在每一頁右上方新增詳細圖例 (含統計數量)
        for page in doc:
            x_start = 450
            y_start = 20
            
            # 繪製半透明底框，避免文字與背景混在一起
            bg_rect = fitz.Rect(x_start - 5, y_start - 5, x_start + 115, y_start + 65)
            page.draw_rect(bg_rect, color=None, fill=(1, 1, 1), fill_opacity=0.8)
            
            # 繪製標題
            page.insert_text((x_start, y_start + 5), "Review Summary:", fontsize=10, color=(0,0,0))
            
            for i, (etype, ecolor) in enumerate(COLOR_MAP.items()):
                current_y = y_start + 20 + (i * 15)
                
                # 畫顏色標示方塊
                rect_icon = fitz.Rect(x_start, current_y - 8, x_start + 10, current_y + 2)
                shape = page.new_shape()
                shape.draw_rect(rect_icon)
                shape.finish(fill=ecolor, color=ecolor)
                shape.commit()
                
                # 繪製文字說明：類別 + 數量 (例如: Spelling: 3)
                label = f"{etype.capitalize()}: {error_counts[etype]}"
                page.insert_text((x_start + 15, current_y), label, fontsize=9, color=(0,0,0))
            
        doc.save(output_pdf)
        doc.close()
        print(f"✨ 全份文件分析完成！已標記 {sum(error_counts.values())} 處錯誤，儲存至: {output_pdf}")