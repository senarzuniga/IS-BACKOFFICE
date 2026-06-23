"""
Memoria permanente del sistema de inteligencia de conocimiento
- Nivel 1: Repositorio documental (archivos)
- Nivel 2: Base de conocimiento estructurada (SQLite)
- Nivel 3: Base vectorial RAG (ChromaDB)
"""

import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except Exception:
    chromadb = None
    Settings = None
    CHROMADB_AVAILABLE = False

from ..models.data_models import KnowledgeItem, Source, ConfidenceLevel


class KnowledgeMemory:
    """Sistema de memoria de tres niveles"""
    
    def __init__(self, base_path: str = "data/knowledge_memory"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Nivel 2: SQLite para conocimiento estructurado
        self.db_path = self.base_path / "knowledge.db"
        self._init_db()
        
        # Nivel 3: ChromaDB para búsquedas vectoriales (RAG)
        self.chroma_path = self.base_path / "chroma"
        self.chroma_path.mkdir(exist_ok=True)
        self.chroma_client = None
        if CHROMADB_AVAILABLE:
            try:
                # Persist directory configuration (works with modern chromadb)
                self.chroma_client = chromadb.Client(Settings(persist_directory=str(self.chroma_path)))
            except Exception:
                try:
                    self.chroma_client = chromadb.Client()
                except Exception:
                    self.chroma_client = None
        self._init_chroma()
    
    def _init_db(self):
        """Inicializa la base de datos SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    category TEXT,
                    subcategory TEXT,
                    summary TEXT,
                    content TEXT,
                    confidence REAL,
                    validated INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    version INTEGER,
                    project TEXT,
                    source_urls TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    knowledge_id TEXT,
                    url TEXT,
                    title TEXT,
                    author TEXT,
                    level INTEGER,
                    confidence REAL,
                    extracted_at TEXT,
                    FOREIGN KEY (knowledge_id) REFERENCES knowledge_items(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    knowledge_id TEXT,
                    entity_type TEXT,
                    entity_value TEXT,
                    FOREIGN KEY (knowledge_id) REFERENCES knowledge_items(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    knowledge_id TEXT,
                    tag TEXT,
                    FOREIGN KEY (knowledge_id) REFERENCES knowledge_items(id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_items(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_project ON knowledge_items(project)")
    
    def _init_chroma(self):
        """Inicializa ChromaDB para RAG"""
        if not self.chroma_client:
            self.collection = None
            return
        try:
            # create or get collection
            try:
                self.collection = self.chroma_client.get_collection(name="knowledge_vectors")
            except Exception:
                self.collection = self.chroma_client.create_collection(name="knowledge_vectors")
        except Exception:
            self.collection = None
    
    def save_knowledge(self, item: KnowledgeItem) -> str:
        """Guarda un elemento de conocimiento en los tres niveles"""
        if not item.id:
            item.id = hashlib.md5(f"{item.title}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO knowledge_items 
                (id, title, category, subcategory, summary, content, confidence, validated, 
                 created_at, updated_at, version, project, source_urls)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.id, item.title, item.category, item.subcategory, 
                item.summary, item.content, item.confidence, 
                1 if item.validated else 0,
                item.created_at.isoformat(),
                datetime.now().isoformat(),
                item.version, item.project,
                json.dumps([s.url for s in item.sources])
            ))
            conn.execute("DELETE FROM sources WHERE knowledge_id = ?", (item.id,))
            for source in item.sources:
                conn.execute("""
                    INSERT INTO sources (knowledge_id, url, title, author, level, confidence, extracted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (item.id, source.url, source.title, source.author, getattr(source.level, 'value', None), source.confidence, source.extracted_at.isoformat()))
            conn.execute("DELETE FROM entities WHERE knowledge_id = ?", (item.id,))
            for entity in item.entities:
                conn.execute("INSERT INTO entities (knowledge_id, entity_type, entity_value) VALUES (?, ?, ?)", (item.id, entity.get('type', ''), entity.get('value', '')))
            conn.execute("DELETE FROM tags WHERE knowledge_id = ?", (item.id,))
            for tag in item.tags:
                conn.execute("INSERT INTO tags (knowledge_id, tag) VALUES (?, ?)", (item.id, tag))
        # Nivel 3: ChromaDB
        if self.collection is not None:
            try:
                self.collection.add(
                    ids=[item.id],
                    documents=[item.content],
                    metadatas=[{
                        'title': item.title,
                        'category': item.category,
                        'project': item.project or '',
                        'confidence': item.confidence,
                        'validated': item.validated
                    }]
                )
            except Exception as e:
                print(f"Error en ChromaDB: {e}")
        return item.id
    
    def search_knowledge(self, query: str, category: Optional[str] = None, 
                         project: Optional[str] = None, top_k: int = 10) -> List[Dict]:
        """Búsqueda semántica en la base de conocimiento"""
        if self.collection is None:
            return []
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
            )
            items = []
            if results and results.get('ids'):
                ids = results['ids'][0]
                metadatas = results.get('metadatas', [[]])[0]
                documents = results.get('documents', [[]])[0]
                distances = results.get('distances', [[]])[0] if 'distances' in results else [0]*len(ids)
                for i, id in enumerate(ids):
                    items.append({
                        'id': id,
                        'title': metadatas[i].get('title', ''),
                        'category': metadatas[i].get('category', ''),
                        'project': metadatas[i].get('project', ''),
                        'confidence': metadatas[i].get('confidence', 0.5),
                        'validated': metadatas[i].get('validated', False),
                        'snippet': documents[i][:500] if i < len(documents) else '',
                        'score': 1 - distances[i] if i < len(distances) else 0.5
                    })
            return items
        except Exception as e:
            print(f"Error en búsqueda vectorial: {e}")
            return []
    
    def search_structured(self, query: str, category: Optional[str] = None,
                          project: Optional[str] = None) -> List[Dict]:
        """Búsqueda estructurada en SQLite (keywords)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            sql = """
                SELECT id, title, category, subcategory, summary, confidence, validated, project
                FROM knowledge_items
                WHERE (title LIKE ? OR content LIKE ?)
            """
            params = [f'%{query}%', f'%{query}%']
            if category:
                sql += " AND category = ?"
                params.append(category)
            if project:
                sql += " AND project = ?"
                params.append(project)
            sql += " ORDER BY confidence DESC LIMIT 20"
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]
    
    def get_knowledge_item(self, id: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM knowledge_items WHERE id = ?", (id,)).fetchone()
            if not row:
                return None
            result = dict(row)
            result['source_urls'] = json.loads(result['source_urls']) if result['source_urls'] else []
            sources = conn.execute("SELECT * FROM sources WHERE knowledge_id = ?", (id,)).fetchall()
            result['sources'] = [dict(s) for s in sources]
            entities = conn.execute("SELECT entity_type, entity_value FROM entities WHERE knowledge_id = ?", (id,)).fetchall()
            result['entities'] = [dict(e) for e in entities]
            tags = conn.execute("SELECT tag FROM tags WHERE knowledge_id = ?", (id,)).fetchall()
            result['tags'] = [t['tag'] for t in tags]
            return result
    
    def get_stats(self) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM knowledge_items").fetchone()[0]
            by_category = conn.execute("SELECT category, COUNT(*) FROM knowledge_items GROUP BY category").fetchall()
            validated = conn.execute("SELECT COUNT(*) FROM knowledge_items WHERE validated = 1").fetchone()[0]
            collection_size = 0
            try:
                if self.collection is not None and hasattr(self.collection, 'count'):
                    collection_size = self.collection.count()
            except Exception:
                collection_size = 0
            return {
                'total_items': total,
                'validated_items': validated,
                'by_category': dict(by_category),
                'collection_size': collection_size
            }
