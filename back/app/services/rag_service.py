import asyncio
import logging
import os
from typing import List, Dict, Any, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.base import DocumentContent
from app.repositories.document_content_repository import DocumentContentRepository, DocumentContentStreamRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RagService:
    def __init__(self, document_content_repository: DocumentContentStreamRepository):
        self.document_content_repository = document_content_repository

        self.documents: List[str] = []
        self.document_metadata: List[Dict[str, Any]] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.document_vectors = None

        logger.info("Simple RAG инициализирован")
    
    async def load_all_documents(self):
        total_chunks = 0
        try:
            async for text in self.document_content_repository.stream_all():
                if not text or len(text) == 0:
                    continue

                logger.info(f"Прочитан файл размером {len(text)} символов")

                chunks = self.split_content(text)
                category = self.extract_category_from_content(text)

                for i, chunk in enumerate(chunks):
                    self.documents.append(chunk)
                    self.document_metadata.append({
                        "chunk": i + 1,
                        "category": category,
                        "is_title": i == 0
                    })
                    total_chunks += 1

                logger.info(f"Добавлено {len(chunks)} чанков")
        except asyncio.CancelledError:
            return False
        
        print(f"Всего загружено документов: {len(self.documents)}")
        self.build_vector_store()

        print("RAG CREATED")
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
    
    def extract_category_from_content(self, content: str) -> str:
        """Пытается определить категорию (заголовок) из содержимого документа"""
        if not content:
            return "ОБЩИЕ"
        
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            return "ОБЩИЕ"
        
        header = lines[0]
        if len(header) > 100:
            header = header[:100] + "..."
        return header.upper()
    
    def enhanced_search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Поиск по векторам с учетом категорий и структуры документа"""
        if not self.documents:
            logger.warning("База документов пуста, попробуйте загрузить документы")
            return []
        
        self._ensure_vector_store_ready()
        if self.document_vectors is None or self.vectorizer is None:
            logger.error("Векторное хранилище не инициализировано")
            return []
        
        query_lower = query.lower().strip()
        query_words = [w for w in query_lower.split() if len(w) > 2]
        
        query_variants = self.generate_query_variants(query)
        logger.info(f"Варианты запроса: {query_variants[:5]}...")
        
        query_vector = self.vectorize_query(query_variants)
        if query_vector is None:
            logger.warning("Не удалось векторизовать запрос")
            return []
        
        similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
        
        # Минимальный порог схожести для фильтрации слабых совпадений
        min_similarity_threshold = 0.01
        
        expected_category = self._infer_expected_category(similarities, min_similarity_threshold)
        if expected_category:
            logger.info(f"Ожидаемая категория: {expected_category}")
        else:
            logger.info("Ожидаемая категория не выявлена")
        
        scored_results = []
        for idx, similarity in enumerate(similarities):
            # Фильтруем слабые совпадения
            if similarity < min_similarity_threshold:
                continue
            
            metadata = self.document_metadata[idx]
            doc_text = self.documents[idx]
            doc_lower = doc_text.lower()
            current_category = metadata["category"]
            is_title = metadata["is_title"]
            
            # Проверка точного совпадения ключевых слов запроса
            keyword_matches = 0
            for word in query_words:
                if word in doc_lower:
                    keyword_matches += 1
            
            score = self.calculate_enhanced_score(
                similarity,
                current_category,
                expected_category,
                is_title,
                keyword_matches,
                len(query_words)
            )
            
            scored_results.append({
                "content": doc_text,
                "score": score,
                "similarity": similarity,
                "category": current_category,
                "is_title": is_title,
                "metadata": metadata
            })
        
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Логируем топ результаты для отладки
        if scored_results:
            logger.info(f"Топ-5 результатов по score:")
            for i, result in enumerate(scored_results[:5], 1):
                logger.info(f"  {i}. Score: {result['score']:.3f}, Similarity: {result['similarity']:.4f}, "
                          f"Category: {result['category'][:50]}")
        
        unique_results = []
        seen_content = set()
        for result in scored_results:
            content_hash = hash(result["content"][:150])
            if content_hash in seen_content:
                continue
            seen_content.add(content_hash)
            unique_results.append(result)
            if len(unique_results) >= max_results:
                break
        
        logger.info(f"Найдено {len(unique_results)} результатов для: '{query}'")
        logger.info('Вывод инструкций >>>')
        for instruction in unique_results:
            logger.info(instruction)
        logger.info('<<<')
        
        return unique_results
    
    def calculate_enhanced_score(self, similarity: float, current_category: str,
                                 expected_category: Optional[str], is_title: bool,
                                 keyword_matches: int, total_query_words: int) -> float:
        """Комбинация косинусной близости и эвристик категорий"""
        # Базовый score основан на косинусной близости (основной фактор)
        score = similarity * 200
        
        # Большой бонус за точное совпадение ключевых слов запроса
        if total_query_words > 0:
            keyword_ratio = keyword_matches / total_query_words
            if keyword_ratio >= 1.0:  # Все слова найдены
                score += 100
            elif keyword_ratio >= 0.5:  # Хотя бы половина слов найдена
                score += 50
            elif keyword_matches > 0:  # Хотя бы одно слово найдено
                score += 20
        
        # Бонус за совпадение категории (но меньший, чем за ключевые слова)
        if expected_category and current_category == expected_category:
            score += 15
        elif expected_category and current_category != expected_category:
            score -= 5
        
        # Небольшой бонус за заголовок
        if is_title:
            score += 5
        
        return score
    
    def generate_query_variants(self, query: str) -> List[str]:
        """Генерация вариантов запроса с синонимами"""
        query_lower = query.lower()
        variants = [query, query_lower]
        
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
        
        for original, synonym_list in synonyms.items():
            if original in query_lower:
                for synonym in synonym_list:
                    variants.append(query_lower.replace(original, synonym))
        
        words = query_lower.split()
        if len(words) > 1:
            main_words = [word for word in words if word not in ['в', 'на', 'при', 'по', 'у', 'с', 'над']]
            if main_words:
                variants.append(' '.join(main_words))
        
        return list(set(variants))

    def build_vector_store(self):
        """Создание TF-IDF индекса для всех документов"""
        if not self.documents:
            logger.warning("Нет документов для построения векторного индекса")
            return
        
        logger.info("Строим TF-IDF индекс для базы знаний")
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            token_pattern=r"(?u)\b[а-яa-z0-9][а-яa-z0-9]+\b",
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,  # Игнорируем слишком частые слова (стоп-слова)
            sublinear_tf=True  # Логарифмическое масштабирование TF для лучшей дискриминации
        )
        self.document_vectors = self.vectorizer.fit_transform(self.documents)
        logger.info(f"TF-IDF индекс построен: {self.document_vectors.shape}")

    def vectorize_query(self, query_variants: List[str]):
        """Преобразование запроса в векторное представление"""
        if not query_variants or self.vectorizer is None:
            return None
        
        # Приоритизируем оригинальный запрос, повторяя его несколько раз
        # Это помогает для коротких запросов
        if len(query_variants) > 0:
            original = query_variants[0]
            # Повторяем оригинальный запрос 3 раза для усиления его веса
            weighted_query = " ".join([original] * 3 + query_variants[1:])
        else:
            weighted_query = " ".join(query_variants)
        
        try:
            return self.vectorizer.transform([weighted_query])
        except ValueError as exc:
            logger.error(f"Ошибка векторизации запроса: {exc}")
            return None

    def _ensure_vector_store_ready(self):
        """Проверяет готовность векторного индекса, строит при необходимости"""
        if self.vectorizer is None or self.document_vectors is None:
            logger.info("Векторное хранилище отсутствует, создаем заново")
            self.build_vector_store()
    
    def _infer_expected_category(self, similarities, min_threshold: float = 0.01) -> Optional[str]:
        """Определяет наиболее вероятную категорию по наиболее близкому документу"""
        if similarities.size == 0:
            return None
        
        best_index = similarities.argmax()
        if similarities[best_index] < min_threshold:
            return None
        
        return self.document_metadata[best_index]["category"]
    
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