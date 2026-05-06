import csv
import re
import os

# Karakalpak Cyrillic to Latin mapping
kk_map = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j', 'з': 'z',
    'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
    'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 's', 'ч': 'ch', 'ш': 'sh', 'щ': 'sh',
    'ъ': '\'', 'ы': 'ı', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'ғ': 'ǵ', 'ў': 'w', 'қ': 'q', 'ң': 'ń', 'ө': 'ó', 'ү': 'ú', 'ә': 'á', 'і': 'i', 'ҳ': 'h',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'J', 'З': 'Z',
    'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R',
    'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'X', 'Ц': 'S', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sh',
    'Ъ': '\'', 'Ы': 'Í', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    'Ғ': 'Ǵ', 'Ў': 'W', 'Қ': 'Q', 'Ң': 'Ń', 'Ө': 'Ó', 'Ү': 'Ú', 'Ә': 'Á', 'І': 'I', 'Ҳ': 'H'
}

# Uzbek Cyrillic to Latin mapping
uz_map = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j', 'з': 'z',
    'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
    'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sh',
    'ъ': '\'', 'ы': 'i', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'ғ': 'g\'', 'ў': 'o\'', 'қ': 'q', 'ҳ': 'h',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'J', 'З': 'Z',
    'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R',
    'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'X', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sh',
    'Ъ': '\'', 'Ы': 'I', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    'Ғ': 'G\'', 'Ў': 'O\'', 'Қ': 'Q', 'Ҳ': 'H'
}

def transliterate_word(word, mapping, lang):
    res = ""
    for i, char in enumerate(word):
        lower_char = char.lower()
        if lower_char == 'е':
            if i == 0 or word[i-1].lower() in 'аеёиоуыэюяъь':
                res += 'Ye' if char.isupper() else 'ye'
                continue
        if lang == 'uz':
            if lower_char == 'ц':
                if i > 0 and word[i-1].lower() in 'аеёиоуыэюя':
                    res += 'Ts' if char.isupper() else 'ts'
                else:
                    res += 'S' if char.isupper() else 's'
                continue
                
        if char in mapping:
            res += mapping[char]
        else:
            res += char
            
    return res

def detect_language(text):
    kk_markers = ['қарақалпақ', 'нөкис', 'бөлим', 'орай', 'министрлик', 'ҳәм', 'хызмет', 'мәкеме', 'мәкән', 'аўыл', 'жәмийет', 'кәрхана', 'басқарма', 'бойынша', 'мектеп', 'мәмлекетлик', 'қәнийге', 'илим', 'тәрбия', 'аймақ', 'гриди']
    uz_markers = ['қорақалпоғ', 'нукус', 'бўлим', 'марказ', 'вазирлик', 'ва ', 'хизмат', 'муассаса', 'маҳалла', 'қишлоқ', 'жамият', 'корхона', 'бошқарма', 'бўйича', 'мактаб', 'давлат', 'ихтисос', 'илмий', 'тарбия', 'ҳудуд', 'ўсмир', 'йўл']
    
    text_lower = text.lower()
    
    if re.search(r'[әөүң]', text_lower):
        return 'kk'
        
    kk_score = sum(1 for marker in kk_markers if marker in text_lower)
    uz_score = sum(1 for marker in uz_markers if marker in text_lower)
    
    if kk_score > uz_score:
        return 'kk'
    elif uz_score > kk_score:
        return 'uz'
        
    # If tie or 0 score, check for 'ў' and 'ғ' context if possible
    # 'ў' in kk is 'w' (consonant), in uz is 'o'' (vowel)
    if 'ў' in text_lower:
        # if next to a consonant, it's a vowel -> Uzbek
        if re.search(r'[бвгджзйклмнпрстфхцчшщ]\s*ў', text_lower) or re.search(r'ў\s*[бвгджзйклмнпрстфхцчшщ]', text_lower):
             # Actually 'ўсмир' -> 'ў' is start, 'с' is consonant -> it's a vowel -> uz
             return 'uz'
             
    if 'ҳ' in text_lower:
        # 'ҳ' is heavily used in Uzbek, rare in Karakalpak except 'ҳәм', 'ҳәким'
        if not re.search(r'ҳәм|ҳәким|ҳайўан', text_lower):
            return 'uz'
            
    # Defaulting based on common Uzbek endings if no KK markers
    if re.search(r'лари$|си$', text_lower.strip()):
        return 'uz'
        
    return 'kk'

def transliterate(text):
    if not re.search(r'[А-Яа-яЁё]', text):
        return text 
        
    lang = detect_language(text)
    mapping = kk_map if lang == 'kk' else uz_map
    
    # Split by non-alphanumeric (Cyrillic) but keeping words together
    # Use re.split to keep separators so we can reconstruct the string
    parts = re.split(r'([А-Яа-яЁёӘәӨөҮүҢңҚқҒғЎўҲҳІі]+)', text)
    result = []
    for part in parts:
        if re.match(r'^[А-Яа-яЁёӘәӨөҮүҢңҚқҒғЎўҲҳІі]+$', part):
            result.append(transliterate_word(part, mapping, lang))
        else:
            result.append(part)
    return ''.join(result)

def process_csv(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f_in, open(output_path, 'w', encoding='utf-8', newline='') as f_out:
        reader = csv.reader(f_in, delimiter=';')
        writer = csv.writer(f_out, delimiter=';')
        
        for row in reader:
            new_row = [transliterate(cell) for cell in row]
            writer.writerow(new_row)

if __name__ == "__main__":
    input_file = r"d:\Projects\2026\TELEGRAM BOT\INN\Нокис хамме мекемелер.csv"
    output_file = r"d:\Projects\2026\TELEGRAM BOT\INN\Нокис хамме мекемелер_latin.csv"
    process_csv(input_file, output_file)
    print("Transliteration complete. Saved to:", output_file)
