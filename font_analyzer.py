import json
import numpy as np

def check_height_consistency(line):
    heights = [word['height'] for word in line]
    if len(heights) < 2: return 0
    if np.std(heights) >= 0.5: return 30
    return 0

def check_alignment_consistency(line):
    tops = [word['top'] for word in line]
    if len(tops) < 2: return 0
    if np.std(tops) > 1.0: return 30
    return 0

def check_spacing_consistency(line):
    if len(line) < 2: return 0
    line.sort(key=lambda w: w['left'])
    spaces = []
    for i in range(len(line) - 1):
        space = line[i+1]['left'] - (line[i]['left'] + line[i]['width'])
        if space > 0: spaces.append(space)
    if len(spaces) < 1: return 0
    avg_space = np.mean(spaces)
    if avg_space > 0 and np.std(spaces) / avg_space > 0.5: return 20
    return 0

def analyze_document_font(json_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            ocr_result = json.load(f)
    except FileNotFoundError:
        return {"error": f"파일을 찾을 수 없습니다: {json_file_path}"}

    fields = ocr_result.get("images", [{}])[0].get("fields", [])
    if not fields:
        return {"error": "분석할 텍스트(fields)가 없습니다."}

    processed_words = []
    for field in fields:
        vertices = field.get("boundingPoly", {}).get("vertices", [])
        if len(vertices) == 4:
            processed_words.append({
                'text': field.get("inferText", ""),
                'top': (vertices[0]['y'] + vertices[1]['y']) / 2,
                'height': ((vertices[2]['y'] + vertices[3]['y']) / 2) - ((vertices[0]['y'] + vertices[1]['y']) / 2),
                'left': vertices[0]['x'],
                'width': vertices[1]['x'] - vertices[0]['x']
            })
    
    processed_words.sort(key=lambda w: w['top'])

    lines = []
    if processed_words:
        current_line = [processed_words[0]]
        for word in processed_words[1:]:
            base_word = current_line[0]
            if abs(word['top'] - base_word['top']) < base_word['height'] * 0.5:
                current_line.append(word)
            else:
                lines.append(current_line)
                current_line = [word]
        lines.append(current_line)

    total_score = 0
    for line in lines:
        total_score += check_height_consistency(line)
        total_score += check_alignment_consistency(line)
        total_score += check_spacing_consistency(line)
    
    decision = "Safe"
    if total_score > 50:
        decision = "Danger"
    elif total_score > 20:
        decision = "Warning"

    return {
        "score": total_score,
        "decision": decision
    }

if __name__ == "__main__":
    result_file = "ocr_result.json"
    analysis_result = analyze_document_font(result_file)
    print("--- 최종 모듈 테스트 결과 ---")
    print(analysis_result)