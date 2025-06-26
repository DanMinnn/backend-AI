import re
from typing import List, Tuple


class ContentFilter:
    def __init__(self):
        # Danh sách từ ngữ nhạy cảm (có thể mở rộng)
        self.inappropriate_words = [
            # Từ chửi thề tiếng Việt
            'đmm', 'dmm', 'đm', 'dm', 'vcl', 'vkl', 'cc', 'clmm', 'clm', 
            'đcm', 'dcm', 'đcmm', 'dcmm', 'mlb', 'đb', 'db', 'cặc', 'lồn',
            'buồi', 'đéo', 'deo', 'shit', 'fuck', 'damn', 'bitch', 'asshole',
            'stupid', 'idiot', 'moron', 'retard', 'gay', 'lesbian',
            # Từ khiếm nhã
            'ngu', 'đần', 'khùng', 'điên', 'mất dạy', 'vô học', 'thô lỗ',
            'chó', 'lợn', 'heo', 'súc vật', 'con đĩ', 'đĩ', 'cave', 'gái bán hoa'
        ]
        
        # Pattern để phát hiện từ ngữ bị che hoặc viết tắt
        self.pattern_replacements = {
            r'd[*@#$%^&!]+m': 'đm',
            r'v[*@#$%^&!]+l': 'vcl',
            r'c[*@#$%^&!]+c': 'cc',
            r'f[*@#$%^&!]+k': 'fuck',
            r's[*@#$%^&!]+t': 'shit'
        }

    def is_inappropriate(self, text: str) -> Tuple[bool, List[str]]:
        """
        Kiểm tra nội dung có chứa từ ngữ không phù hợp hay không
        Returns: (is_inappropriate, detected_words)
        """
        text_lower = text.lower()
        detected_words = []
        
        # Kiểm tra từ ngữ trực tiếp
        for word in self.inappropriate_words:
            if word in text_lower:
                detected_words.append(word)
        
        # Kiểm tra pattern che từ
        for pattern, replacement in self.pattern_replacements.items():
            if re.search(pattern, text_lower):
                detected_words.append(replacement)
        
        return len(detected_words) > 0, detected_words