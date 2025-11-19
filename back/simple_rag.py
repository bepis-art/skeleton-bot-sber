import logging
import os
from typing import List, Dict, Any


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleRAG:
    def __init__(self, documents_path: str = "documents"):
        self.documents_path = documents_path
        self.documents = []
        self.document_metadata = []
        
        # Ключевые слова для категорий
        self.category_keywords = {
            'БЫТОВЫЕ': ['квартира', 'дом', 'быт', 'газ', 'пожар', 'затопление', 'электричество', 'дым', 'огонь', 'запах', 'кухня', 'ванная'],
            'БПЛА': ['дрон', 'бпла', 'беспилотник', 'воздушный', 'квадрокоптер', 'атака', 'обнаружить', 'небо', 'полет', 'город', 'воздух'],
            'ПРИРОДНЫЕ': ['землетрясение', 'наводнение', 'ураган', 'природный', 'стихия', 'шторм', 'толчки', 'паводок', 'подтопление', 'ливень', 'буря'],
            'ТЕХНОГЕННЫЕ': ['химический', 'радиация', 'радиационный', 'радиационная', 'авария', 'завод', 'производство', 'взрыв', 'промышленный', 'опасный', 'ядовитый', 'химическая']
        }
        
        logger.info("Simple RAG инициализирован")
    
    def load_all_documents(self):
        """Загрузка всех документов с разными стратегиями"""
        if not os.path.exists(self.documents_path):
            logger.error(f"Папка {self.documents_path} не найдена")
            return False
        
        text_files = [f for f in os.listdir(self.documents_path) if f.endswith('.txt')]
        logger.info(f"Найдено файлов: {len(text_files)}")
        
        total_chunks = 0
        for filename in text_files:
            file_path = os.path.join(self.documents_path, filename)
            try:
                # Чтение файла с разными кодировками
                content = self.read_file_safe(file_path)
                if not content:
                    continue
                
                logger.info(f"Файл {filename} прочитан, размер: {len(content)} символов")
                
                # Разные стратегии разбиения
                chunks = self.split_content(content)
                
                for i, chunk in enumerate(chunks):
                    self.documents.append(chunk)
                    self.document_metadata.append({
                        "source": filename,
                        "chunk": i + 1,
                        "category": self.get_category(filename),
                        "is_title": i == 0  # Первый чанк считается заголовком
                    })
                    total_chunks += 1
                
                logger.info(f"Добавлено {len(chunks)} чанков из {filename}")
                
            except Exception as e:
                logger.error(f"Ошибка при загрузке {filename}: {e}")
                continue
        
        logger.info(f"Всего загружено документов: {len(self.documents)}")
        return True
    
    def read_file_safe(self, file_path: str) -> str:
        """Безопасное чтение файла с разными кодировками"""
        encodings = ['utf-8', 'cp1251', 'windows-1251', 'latin1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read().strip()
                if content and len(content) > 10:
                    return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Ошибка с кодировкой {encoding}: {e}")
                continue
        
        logger.warning(f"Не удалось прочитать файл {file_path}")
        return ""
    
    def split_content(self, content: str) -> List[str]:
        """Разные стратегии разбиения контента"""
        chunks = []
        
        # Стратегия 1: Разбиение по двойным переносам строк
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        for paragraph in paragraphs:
            if len(paragraph) > 30:
                chunks.append(paragraph)
        
        # Стратегия 2: Если мало параграфов, разбиваем по одиночным переносам
        if len(chunks) < 2:
            lines = [line.strip() for line in content.split('\n') if len(line.strip()) > 30]
            chunks.extend(lines)
        
        # Стратегия 3: Если все еще мало, разбиваем по точкам
        if len(chunks) < 2 and len(content) > 100:
            sentences = [s.strip() + '.' for s in content.split('.') if len(s.strip()) > 20]
            chunks.extend(sentences)
        
        return chunks
    
    def get_category(self, filename: str) -> str:
        """Определение категории по имени файла"""
        filename_lower = filename.lower()
        if 'domestic' in filename_lower:
            return 'БЫТОВЫЕ'
        elif 'drone' in filename_lower:
            return 'БПЛА'
        elif 'natural' in filename_lower:
            return 'ПРИРОДНЫЕ'
        elif 'techno' in filename_lower:
            return 'ТЕХНОГЕННЫЕ'
        else:
            return 'ОБЩИЕ'
    
    def enhanced_search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Улучшенный поиск с учетом категорий и заголовков"""
        if not self.documents:
            logger.warning("База документов пуста")
            return []
        
        # Определяем ожидаемую категорию по запросу
        expected_category = self.determine_expected_category(query)
        logger.info(f"Ожидаемая категория: {expected_category}")
        
        # Создаем варианты запроса
        query_variants = self.generate_query_variants(query)
        logger.info(f"Варианты запроса: {query_variants[:5]}...")  # Показываем только первые 5
        
        results = []
        
        for i, doc in enumerate(self.documents):
            doc_lower = doc.lower()
            current_category = self.document_metadata[i]["category"]
            is_title = self.document_metadata[i]["is_title"]
            
            score = self.calculate_enhanced_score(
                query_variants, doc_lower, current_category, 
                expected_category, is_title, query.lower()
            )
            
            if score > 5:  # Повышаем порог для уменьшения шума
                results.append({
                    "content": doc,
                    "score": score,
                    "source": self.document_metadata[i]["source"],
                    "category": current_category,
                    "is_title": is_title,
                    "metadata": self.document_metadata[i]
                })
        
        # Сортируем по убыванию релевантности
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Убираем дубликаты по содержанию
        unique_results = []
        seen_content = set()
        for result in results:
            content_hash = hash(result["content"][:100])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        final_results = unique_results[:max_results]
        logger.info(f"Найдено {len(final_results)} результатов для: '{query}'")

        logger.info('Вывод инструкций >>>')
        for instruction in final_results:
            logger.info(instruction)
        logger.info('<<<')

        return final_results
    
    def determine_expected_category(self, query: str) -> str:
        """Определение ожидаемой категории по запросу"""
        query_lower = query.lower()
        
        category_scores = {
            'БЫТОВЫЕ': 0,
            'БПЛА': 0,
            'ПРИРОДНЫЕ': 0,
            'ТЕХНОГЕННЫЕ': 0
        }
        
        # Подсчет ключевых слов для каждой категории
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    category_scores[category] += 1
        
        # Определяем категорию с максимальным счетом
        max_score = 0
        expected_category = 'ОБЩИЕ'
        
        for category, score in category_scores.items():
            if score > max_score:
                max_score = score
                expected_category = category
        
        return expected_category
    
    def calculate_enhanced_score(self, query_variants, doc_text, current_category, 
                               expected_category, is_title, original_query):
        """Улучшенный расчет релевантности"""
        score = 0
        
        # Бонус за совпадение в заголовке (первый чанк)
        if is_title:
            for variant in query_variants:
                if variant in doc_text:
                    score += 25  # Большой бонус за заголовок
        
        # Проверяем все варианты запроса в основном тексте
        for variant in query_variants:
            variant_lower = variant.lower()
            
            # Точное совпадение фразы
            if variant_lower in doc_text:
                score += 15 * len(variant.split())  # Вес за полное совпадение
            
            # Совпадение отдельных слов
            words = variant_lower.split()
            for word in words:
                if len(word) > 2:
                    if word in doc_text:
                        score += 8  # Увеличиваем вес за отдельные слова
        
        # Бонус за правильную категорию
        if current_category == expected_category:
            score += 20
        else:
            score -= 10  # Штраф за неправильную категорию
        
        # Бонус за ключевые слова категории в документе
        if expected_category in self.category_keywords:
            for keyword in self.category_keywords[expected_category]:
                if keyword in doc_text:
                    score += 5
        
        # Бонус за точное совпадение с оригинальным запросом
        if original_query in doc_text:
            score += 30
        
        return score
    
    def generate_query_variants(self, query: str) -> List[str]:
        """Генерация вариантов запроса с синонимами"""
        query_lower = query.lower()
        variants = [query, query_lower]
        
        # Синонимы и связанные термины
        synonyms = {
            'пожар': ['огонь', 'возгорание', 'пламя', 'дым'],
            'дрон': ['бпла', 'беспилотник', 'квадрокоптер', 'дроны'],
            'атака': ['нападение', 'угроза', 'обстрел', 'налет'],
            'землетрясение': ['толчки', 'подземные толчки', 'сейсмическая активность'],
            'наводнение': ['паводок', 'затопление', 'подтопление', 'разлив'],
            'авария': ['катастрофа', 'происшествие', 'чп', 'инцидент'],
            'химический': ['отравляющий', 'ядовитый', 'опасный', 'химическая'],
            'газ': ['метан', 'пропан', 'утечка', 'запах'],
            'радиация': ['радиационный', 'радиационная', 'излучение', 'радиоактивный']
        }
        
        # Добавляем варианты с синонимами
        for original, synonym_list in synonyms.items():
            if original in query_lower:
                for synonym in synonym_list:
                    variant = query_lower.replace(original, synonym)
                    variants.append(variant)
        
        # Добавляем варианты без предлогов
        words = query_lower.split()
        if len(words) > 1:
            main_words = [word for word in words if word not in ['в', 'на', 'при', 'по', 'у', 'с', 'над']]
            if main_words:
                variants.append(' '.join(main_words))
        
        return list(set(variants))
    
    def search_emergency_instructions(self, emergency_description: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Основной метод поиска для использования в боте"""
        return self.enhanced_search(emergency_description, max_results)
    
    def get_stats(self):
        """Статистика базы"""
        categories = {}
        for meta in self.document_metadata:
            cat = meta["category"]
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_documents": len(self.documents),
            "categories": categories
        }