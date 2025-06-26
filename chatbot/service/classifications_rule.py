
import hashlib
import re
from typing import Tuple


def setup_classification_rules(self):
    """Setup patterns based on actual document content"""
    # 1. REPAIR & MAINTENANCE SERVICES
    self.repair_patterns = [
            # AC/Air Conditioner
            r'\b(ac|air conditioner|airconditioner|điều hòa|máy lạnh|máy điều hòa|điều hòa không khí)\b.*\b(repair|fix|sửa|maintenance|bảo trì|service|dịch vụ|price|cost|giá|phí|công suất|hp|split|portable|ceiling-mounted)\b',
            r'\b(repair|fix|sửa|maintenance|bảo trì|service|dịch vụ|price|cost|giá|phí|công suất|hp|split|portable|ceiling-mounted)\b.*\b(ac|air conditioner|airconditioner|điều hòa|máy lạnh|máy điều hòa|điều hòa không khí)\b',
            # TV/Television
            r'\b(tv|television|tivi|ti vi|tê vi)\b.*\b(repair|fix|sửa|maintenance|service|dịch vụ|price|cost|giá|phí)\b',
            # Car/Automobile
            r'\b(car|automobile|vehicle|ô tô|xe hơi|xe oto)\b.*\b(repair|fix|sửa|maintenance|service|dịch vụ|price|cost|giá|phí)\b',
            # Electrician
            r'\b(electrician|electrical|electric|thợ điện|điện)\b.*\b(service|work|repair|fix|dịch vụ|sửa|price|cost|giá|phí)\b',
            # Plumber
            r'\b(plumber|plumbing|pipe|thợ ống nước|ống nước|nước)\b.*\b(service|work|repair|fix|dịch vụ|sửa|price|cost|giá|phí)\b',
            # Van/Transport
            r'\b(van|transport|delivery|vận chuyển|giao hàng|chuyển đồ)\b.*\b(service|rental|hire|thuê|dịch vụ|price|cost|giá|phí)\b',
        ]

    # 2. HOME SERVICES
    self.home_service_patterns = [
            # Cleaning
            r'\b(clean|cleaning|house cleaning|home cleaning|dọn dẹp|dọn nhà|vệ sinh|tổng vệ sinh)\b.*\b(service|price|cost|fee|giá|phí|dịch vụ|diện tích|area|m²|phòng|room|phụ thu|additional fee)\b',
            r'\b(service|price|cost|fee|giá|phí|dịch vụ|diện tích|area|m²|phòng|room|phụ thu|additional fee)\b.*\b(clean|cleaning|house cleaning|home cleaning|dọn dẹp|dọn nhà|vệ sinh|tổng vệ sinh)\b',
            # Cooking
            r'\b(cook|cooking|chef|personal chef|nấu ăn|dịch vụ nấu ăn|đầu bếp)\b.*\b(service|price|cost|fee|giá|phí|dịch vụ|book|đặt|số người|people|số món|dishes|phụ thu|additional fee)\b',
            # Labor
            r'\b(labor|labour|worker|general labor|lao động|công nhân|người làm)\b.*\b(service|hire|thuê|dịch vụ|price|cost|giá|phí)\b',
            # Tailor
            r'\b(tailor|tailoring|sewing|may|thợ may|may vá)\b.*\b(service|dịch vụ|price|cost|giá|phí)\b',
        ]

    # 3. POLICY & APP RELATED PATTERNS
    self.policy_app_patterns = [
            # Booking/Scheduling
            r'\b(book|booking|schedule|appointment|đặt lịch|đặt hẹn|hẹn giờ)\b',
            r'\bhow to\b.*\b(book|schedule|đặt lịch|đặt hẹn)\b',
            r'\b(how|cách|như thế nào)\b.*\b(book|schedule|đặt lịch|đặt hẹn)\b',
            r'\b(cancel|cancellation|hủy|hủy đơn|hủy lịch)\b.*\b(booking|schedule|appointment|đặt lịch|đặt hẹn)\b',
            # Cancellation
            r'\b(cancel|cancellation|hủy|hủy đơn|hủy lịch)\b.*\b(policy|fee|charge|chính sách|phí)\b',
            r'\b(policy|fee|charge|chính sách|phí)\b.*\b(cancel|cancellation|hủy|hủy đơn|hủy lịch)\b',
            # Payment
            r'\b(payment|pay|thanh toán|trả tiền)\b.*\b(method|way|how|cách|như thế nào)\b',
            r'\b(cash|tiền mặt|vnpay|hpay|ví điện tử)\b',
            # Refund
            r'\b(refund|hoàn tiền|hoàn lại|trả lại)\b.*\b(policy|how|cách|chính sách)\b',
            r'\b(policy|how|cách|chính sách)\b.*\b(refund|hoàn tiền|hoàn lại|trả lại)\b',
            # Weekend/Time
            r'\b(weekend|saturday|sunday|cuối tuần|24/7|24h)\b.*\b(service|available|support|dịch vụ|có không|hỗ trợ)\b',
            # Account/App
            r'\b(account|login|register|đăng nhập|đăng ký|tài khoản|password|forgot|quên|mật khẩu|delete account|xóa tài khoản)\b',
            r'\b(app|application|ứng dụng)\b.*\b(how|use|sử dụng|cách)\b',
            r'\b(app|application|ứng dụng)\b.*\b(download|tải về|cài đặt|install)\b',
            r'\b(app|application|ứng dụng)\b.*\b(update|cập nhật|version|phiên bản)\b',
            r'\b(app|application|ứng dụng)\b.*\b(features|tính năng|functionality|chức năng)\b',
            r'\b(app|application|ứng dụng)\b.*\b(privacy|security|bảo mật|chính sách bảo mật)\b',
        
        ]

    # Combine patterns
    self.app_related_patterns = (
            self.repair_patterns +
            self.home_service_patterns +
            self.policy_app_patterns
        )

    # General patterns
    self.general_patterns = [
            r'\b(weather|thời tiết|time|giờ)\b',
            r'\b(recipe|công thức|cách nấu)\b',
            r'\b(news|tin tức|newspaper)\b',
            r'\b(travel|du lịch|vacation|nghỉ mát)\b',
            r'\b(food|đồ ăn|ẩm thực|restaurant|nhà hàng)\b',
            r'\b(movie|film|phim|music|nhạc)\b',
            r'\b(health|sức khỏe|medical|y tế)\b',
            r'\b(education|giáo dục|school|trường học)\b',
            r'\b(sports|thể thao|football|bóng đá|basketball|bóng rổ)\b',
            r'\b(shopping|mua sắm|store|cửa hàng)\b',
            r'\b(technology|công nghệ|gadget|thiết bị)\b',
            r'\b(fashion|thời trang|clothing|quần áo)\b',
            r'\b(finance|tài chính|banking|ngân hàng)\b',
            r'\b(real estate|bất động sản|property|tài sản)\b',
        ]
    
def normalize_query(query: str) -> str:
    normalized = query.lower().strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r'[?!.]+$', '', normalized)
        
    # Handle common variations
    normalized = re.sub(r'\bac\b', 'air conditioner', normalized)
    normalized = re.sub(r'\btv\b', 'television', normalized)
    return normalized

def get_query_hash(self, query: str) -> str:
    """Generate hash for query to use as cache key"""
    normalized = normalize_query(query)
    return hashlib.md5(normalized.encode()).hexdigest()

def rule_based_classification(self, query: str) -> Tuple[str, float, list]:
        normalized_query = normalize_query(query)
        
        app_related_matches = []
        general_matches = []
        
        # Check app-related patterns
        for i, pattern in enumerate(self.app_related_patterns):
            if re.search(pattern, normalized_query, re.IGNORECASE):
                app_related_matches.append(f"Pattern_{i}: {pattern}")
        
        # Check general patterns  
        for i, pattern in enumerate(self.general_patterns):
            if re.search(pattern, normalized_query, re.IGNORECASE):
                general_matches.append(f"General_{i}: {pattern}")
        
        app_score = len(app_related_matches)
        general_score = len(general_matches)
        
        if app_score > general_score:
            confidence = min(app_score / max(len(self.app_related_patterns) * 0.1, 1), 1.0)
            return 'app_related', confidence, app_related_matches
        elif general_score > app_score:
            confidence = min(general_score / max(len(self.general_patterns) * 0.1, 1), 1.0)
            return 'general', confidence, general_matches
        else:
            # For home service app, default to app_related when unclear
            return 'app_related', 0.6, ['Default: Home service app']
