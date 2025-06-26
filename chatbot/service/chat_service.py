import json
import logging
import re
from typing import Dict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
import os

from service.content_filter import ContentFilter
from service.classifications_rule import (
    get_query_hash,
    normalize_query,
    rule_based_classification,
    setup_classification_rules
)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  
VECTORSTORE_PATH = os.path.join(BASE_DIR, "vectorstores", "db_faiss")
print(f"Loading vectorstore from: {VECTORSTORE_PATH}")
logging.basicConfig(filename='chatbot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()
class ChatService:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama3-8b-8192"
        )
        self.embeddings = HuggingFaceEmbeddings(
        model_name="keepitreal/vietnamese-sbert",
        model_kwargs={"device": "cpu"},  
        encode_kwargs={"normalize_embeddings": True} 
    )
        self.vector_store = FAISS.load_local(VECTORSTORE_PATH, self.embeddings, allow_dangerous_deserialization=True)
        self.content_filter = ContentFilter()

        #cache intent - responses
        self.intent_cache: Dict[str, str] = {}
        self.response_cache: Dict[str, str] = {}

        # Define deterministic rules
        setup_classification_rules(self)
    def llm_classification_with_constraints(self, query: str) -> str:
        """LLM classification with strict constraints"""
        intent_prompt = ChatPromptTemplate.from_template(
            """You are a STRICT intent classifier for a house cleaning service app.

        CLASSIFICATION RULES:
        1. If query mentions: price, cost, fee, charge, rate + cleaning/house/service → ALWAYS "app_related"
        2. If query mentions: booking, schedule, appointment + cleaning/house/service → ALWAYS "app_related"  
        3. If query mentions: cancel, policy, refund + cleaning/house/service → ALWAYS "app_related"
        4. If query mentions: app, login, account, weekend service → ALWAYS "app_related"
        5. If query about: cooking, recipes, weather, news, travel → ALWAYS "general"

        EXAMPLES:
        - "How much does clean house service cost?" → app_related
        - "What's the price of cleaning service?" → app_related
        - "How to cook pho?" → general
        - "Weather today?" → general

        Query: {query}

        RESPOND WITH ONLY: {{"intent": "app_related"}} OR {{"intent": "general"}} OR {{"intent": "inappropriate_content"}} NO OTHER TEXT.""")
        
        try:
            response = self.llm.invoke(intent_prompt.format(query=query))
            intent_data = json.loads(response.content.strip())
            return intent_data.get('intent', 'app_related')
        except:
            return 'app_related'  # Default to app_related for service app

    def classify_intent(self, query: str) -> str:
        """Classify with caching"""
        query_hash = get_query_hash(self, query)
        
        if query_hash in self.intent_cache:
            return self.intent_cache[query_hash]
        
        intent, confidence, matches = rule_based_classification(self, query)
        # Refine intent for specific categories
        if intent == 'app_related':
            normalized_query = normalize_query(query)
            if re.search(r'\b(clean|cleaning|dọn dẹp|dọn nhà|vệ sinh)\b', normalized_query, re.IGNORECASE):
                intent = 'cleaning_service'
            elif re.search(r'\b(cook|cooking|nấu ăn|đầu bếp)\b', normalized_query, re.IGNORECASE):
                intent = 'cooking_service'
            elif re.search(r'\b(ac|air conditioner|điều hòa|máy lạnh|tivi|ô tô|thợ điện|thợ ống nước|vận chuyển)\b', normalized_query, re.IGNORECASE):
                intent = 'repair_service'
            elif re.search(r'\b(cancel|hủy|refund|hoàn tiền|payment|thanh toán)\b', normalized_query, re.IGNORECASE):
                intent = 'policy'
            elif re.search(r'\b(account|login|register|đăng nhập|đăng ký|password|mật khẩu|delete account|xóa tài khoản|hủy lịch|cancel job|refund|hoàn tiền)\b', normalized_query, re.IGNORECASE):
                intent = 'account'
        # Cache result
        self.intent_cache[query_hash] = intent
        logging.info(f"Classified intent for query '{query}': {intent} (confidence: {confidence})")
        return intent
    
    def keyword_based_classification(self, query: str) -> str:
        """Fallback keyword-based classification"""
        app_keywords = [
           'dọn nhà', 'dọn dẹp', 'vệ sinh', 'giá', 'đặt lịch', 'booking',
            'hủy', 'chính sách', 'dịch vụ', 'cuối tuần', 'thời gian',
            'phí', 'tiền', 'app', 'ứng dụng', 'đăng nhập', 'tài khoản',
            'nấu ăn', 'điều hòa', 'sửa chữa', 'ô tô', 'thợ điện', 'thợ ống nước', 'vận chuyển',
            'giá cả', 'chi phí', 'đặt hẹn', 'hẹn giờ', 'đặt lịch hẹn', 'hủy đơn',
        ]
        
        query_lower = query.lower()
        for keyword in app_keywords:
            if keyword in query_lower:
                return 'app_related'
        return 'general'

    def detect_language(self, query: str) -> str:
        """Detect language of the query"""
        common_english_words = ['hello', 'hi', 'ok', 'thanks', 'sorry']
        normalized_query = normalize_query(query)
        if len(normalized_query.split()) <= 2 and any(word in normalized_query for word in common_english_words):
            return 'vi'
        try:
            from langdetect import detect
            lang = detect(query)
            if lang == 'vi' or lang == 'en':
                return lang
            return 'other'
        except Exception as e:
            logging.error(f"Language detection error: {e}")
            return 'vi'
    
    def calculate_ac_repair_cost(self, ac_type: str, hp: float) -> str:
        """Calculate AC repair cost based on type and horsepower"""
        prices = {
            'portable': 140000,
            'split': 250000,
            'ceiling-mounted': 280000
        }
        base_price = prices.get(ac_type.lower(), 250000) 
        additional = 20000 if hp > 2 else 0
        total = base_price + additional
        return f"{base_price:,} VNĐ (sửa điều hòa {ac_type}) + {additional:,} VNĐ phụ thu (> 2 HP) = {total:,} VNĐ"
    
    # Calculate costs for specific services
    def calculate_cleaning_cost(self, area: float) -> str:
        """Calculate cleaning cost based on area"""
        if area <= 55:
            return f"140.000 VNĐ (gói 2 giờ cho ≤ 55 m²)"
        elif area <= 85:
            price = area * 2000
            return f"Diện tích dưới ≤ 85 m² được tính với giá {price} VNĐ"
        elif area <= 105:
            price = area * 2500
            return f"Diện tích dưới ≤ 105 m² được tính với giá {price} VNĐ"
        else:
            price = area * 2000
            return f"Diện tích dưới ≥ 105 m² được tính với giá {price} VNĐ"

    def calculate_cooking_cost(self, people: int, dishes: int, hours: float) -> str:
        """Calculate cooking cost based on people, dishes, and hours"""
        if people <= 4:
            if hours <= 2:
                base_price = 145000
            else:
                base_price = 220000
            additional = 20000 if dishes <= 3 else 35000
        else:
            if hours <= 2.5:
                base_price = 180000
            else:
                base_price = 250000
            additional = 30000 if dishes <= 3 else 45000
        total = base_price + additional
        return f"{base_price:,} VNĐ (gói {hours} giờ cho {people} người) + {additional:,} VNĐ phụ thu ({dishes} món) = {total:,} VNĐ"

    def handle_combined_query(self, query: str) -> str:
        """Handle complex queries involving multiple services"""
        parts = []
        normalized_query = normalize_query(query)

        # Check for cleaning service
        area_match = re.search(r'(\d+)\s*m²', normalized_query)
        if area_match and re.search(r'\b(clean|cleaning|dọn dẹp|dọn nhà|vệ sinh)\b', normalized_query, re.IGNORECASE):
            area = float(area_match.group(1))
            parts.append(f"Dọn dẹp nhà: {self.calculate_cleaning_cost(area)}")

        # Check for cooking service
        people_match = re.search(r'(\d+)\s*(người|people)', normalized_query)
        dishes_match = re.search(r'(\d+)\s*(món|dishes)', normalized_query)
        hours_match = re.search(r'(\d+\.?\d*)\s*(giờ|hour)', normalized_query)
        if people_match and dishes_match and hours_match:
            people = int(people_match.group(1))
            dishes = int(dishes_match.group(1))
            hours = float(hours_match.group(1))
            if people <= 8:  # Max 8 people per document
                parts.append(f"Nấu ăn: {self.calculate_cooking_cost(people, dishes, hours)}")
            else:
                parts.append("Dịch vụ nấu ăn chỉ hỗ trợ tối đa 8 người. Vui lòng liên hệ hotline 0347596789 để được tư vấn.")

        # Check for AC repair
        ac_match = re.search(r'\b(split|portable|ceiling-mounted)\b', normalized_query, re.IGNORECASE)
        hp_match = re.search(r'(\d+\.?\d*)\s*(hp|công suất)', normalized_query)
        if ac_match and hp_match:
            ac_type = ac_match.group(1)
            hp = float(hp_match.group(1))
            parts.append(f"Sửa điều hòa: {self.calculate_ac_repair_cost(ac_type, hp)}")
            
        if parts:
            return "\n".join(parts)
        return self.handle_app_related_query(query)
    
    def process_query(self, query: str) -> str:

        query_hash = get_query_hash(self, query)
        if query_hash in self.response_cache:
            return self.response_cache[query_hash]
        
        try:
            intent = self.classify_intent(query)
            print(f"Query: '{query}' → Intent: {intent}")
            is_inappropriate, detected_words = self.content_filter.is_inappropriate(query)
            lang = self.detect_language(query)
            if lang == 'other':
                return "Xin lỗi, tôi không hỗ trợ ngôn ngữ này. Vui lòng sử dụng tiếng Việt hoặc tiếng Anh."
            elif is_inappropriate or intent == 'inappropriate_content':
                    return "Xin lỗi, tôi không thể xử lý tin nhắn chứa ngôn từ không phù hợp. Vui lòng sử dụng ngôn từ lịch sự để tôi có thể hỗ trợ bạn tốt hơn.",
            elif intent in ['cleaning_service', 'cooking_service', 'repair_service']:
                response = self.handle_combined_query(query)
            else:
                response = self.handle_app_related_query(query) if intent in ['app_related', 'policy', 'account'] else self.handle_general_query(query)
            # Cache the response
            self.response_cache[query_hash] = response
            return response
                
        except Exception as e:
            print(f"Error processing query: {e}")
            error_response = "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại."
            self.response_cache[query_hash] = error_response
            return error_response


    def handle_app_related_query(self, query: str) -> str:
        """Handle app-related queries with RAG"""
        # Check for upgrading services
        upgrading_services = ['sửa tivi', 'sửa ô tô', 'thợ điện', 'thợ ống nước', 'vận chuyển', 'thợ may', 'làm đẹp', 'chăm sóc', 'làm vườn']
        normalized_query = normalize_query(query)
        if any(s in normalized_query for s in upgrading_services):
            return "Dịch vụ này hiện đang được nâng cấp và chưa có giá cụ thể. Vui lòng liên hệ hotline 0347596789 để được tư vấn."

        # Retrieve relevant documents
        docs = self.vector_store.similarity_search(query, k=3)
        if not docs:
            return "Xin lỗi, tôi không tìm thấy thông tin cụ thể. Vui lòng liên hệ hotline 0347596789 để được hỗ trợ."

        context = "\n".join([doc.page_content for doc in docs])
        rag_prompt = ChatPromptTemplate.from_template(
            """
            SUPPORTING DATA:
            {context}

            USER QUESTION: {query}

            STRICT INSTRUCTIONS:
            - Answer directly to the content, NEVER start with "Here's the answer" or "Answer:" or any introductory phrase.
            - DO NOT repeat the question in the answer.
            - DO NOT include any formatting like "Question:" or "Answer:" in the response.
            - Rely ONLY on the data in the "SUPPORTING DATA" section above.
            - Answer accurately, CONCISELY, and CLEARLY.
            - If pricing calculations are needed, perform the calculations clearly.
            - If no relevant information is found in the data, answer: "Please contact hotline 0347596789 for support."
            - If the question is in Vietnamese → answer in Vietnamese. If in English → answer in English.
            
            REPLY FORMAT: Just provide the direct answer without any preamble or question repetition.
            """
        )
        response = self.llm.invoke(rag_prompt.format(context=context, query=query))
        content = response.content
        content = re.sub(r'^Here is .*?:\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'(Câu hỏi|Question).*?\n', '', content, flags=re.IGNORECASE)
        content = re.sub(r'^(Trả lời|Answer):\s*', '', content, flags=re.IGNORECASE)
        logging.info(f"Query: {query}\nRAG Response: {response.content}\nContext: {context}")

        return content.strip()

    def handle_general_query(self, query: str) -> str:
        """Handle general queries"""
        general_prompt = ChatPromptTemplate.from_template(
            """Answer the following question helpfully: {query}
        STRICT INSTRUCTIONS:
        1. Answer directly to the content, briefly and clearly.
        2. If the question is in Vietnamese → answer in Vietnamese. If in English → answer in English.""")
        
        response = self.llm.invoke(general_prompt.format(query=query))
        return response.content

    def debug_classification(self, query: str) -> Dict:
        """Debug method to understand classification process"""
        normalized = normalize_query(query)
        rule_intent, confidence, matches = rule_based_classification(self, query)
        final_intent = self.classify_intent(query)
        docs = self.vector_store.similarity_search(query, k=3)
        return {
            'original_query': query,
            'normalized_query': normalized,
            'rule_based_intent': rule_intent,
            'rule_confidence': confidence,
            'rule_matches': matches,
            'final_intent': final_intent,
            'is_cached': get_query_hash(query) in self.intent_cache,
            'retrieved_docs': [doc.page_content for doc in docs]
        }

    def clear_cache(self):
        """Clear all caches"""
        self.intent_cache.clear()
        self.response_cache.clear()
    def get_debug_info(self, query: str) -> dict:
        """Method to debug intent classification"""
        intent = self.classify_intent(query)
        keyword_intent = self.keyword_based_classification(query)
        
        return {
            'query': query,
            'llm_intent': intent,
            'keyword_intent': keyword_intent,
            'final_intent': intent
        }