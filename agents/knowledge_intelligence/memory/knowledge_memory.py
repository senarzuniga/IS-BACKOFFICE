"""
Memoria permanente del sistema de inteligencia de conocimiento
- Nivel 1: Repositorio documental (archivos)
- Nivel 2: Base de conocimiento estructurada (SQLite)
- Nivel 3: Base vectorial RAG (ChromaDB)
"""

import json
import sqlite3
import hashlib
from dataclasses import asdict
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

from ..models.data_models import KnowledgeItem, Source, ConfidenceLevel, IndustrialKnowledgeObject


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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS industrial_knowledge_objects (
                    object_id TEXT PRIMARY KEY,
                    object_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    canonical_name TEXT,
                    description TEXT,
                    project TEXT,
                    origin_engine TEXT,
                    confidence REAL,
                    validated INTEGER,
                    version INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    tags_json TEXT,
                    payload_json TEXT,
                    checksum TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS industrial_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_object_id TEXT NOT NULL,
                    target_object_id TEXT,
                    relation_type TEXT NOT NULL,
                    metadata_json TEXT,
                    FOREIGN KEY (source_object_id) REFERENCES industrial_knowledge_objects(object_id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_iko_type ON industrial_knowledge_objects(object_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_iko_project ON industrial_knowledge_objects(project)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_iko_name ON industrial_knowledge_objects(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_iko_rel_source ON industrial_relationships(source_object_id)")
    
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
            industrial_total = conn.execute("SELECT COUNT(*) FROM industrial_knowledge_objects").fetchone()[0]
            industrial_by_type = conn.execute("SELECT object_type, COUNT(*) FROM industrial_knowledge_objects GROUP BY object_type").fetchall()
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
                'collection_size': collection_size,
                'industrial_objects': industrial_total,
                'industrial_by_type': dict(industrial_by_type),
            }

    def upsert_industrial_object(self, obj: IndustrialKnowledgeObject) -> str:
        """Persist canonical industrial knowledge object and sync a searchable knowledge item."""
        if not obj.object_id:
            stable_key = f"{obj.object_type}:{obj.canonical_name or obj.name}:{obj.project or ''}"
            obj.object_id = hashlib.md5(stable_key.encode()).hexdigest()[:20]

        payload = {
            'object_id': obj.object_id,
            'object_type': obj.object_type,
            'name': obj.name,
            'canonical_name': obj.canonical_name or obj.name,
            'description': obj.description,
            'technical_data': obj.technical_data,
            'operational_data': obj.operational_data,
            'commercial_data': obj.commercial_data,
            'maintenance_data': obj.maintenance_data,
            'lifecycle_data': obj.lifecycle_data,
            'kpis': obj.kpis,
            'digital_twin_params': obj.digital_twin_params,
            'simulation_params': obj.simulation_params,
            'benchmark_data': obj.benchmark_data,
            'relationships': obj.relationships,
            'evidence': obj.evidence,
            'sources': [asdict(source) for source in obj.source_refs],
            'tags': obj.tags,
        }
        checksum = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode('utf-8')).hexdigest()
        created_at = obj.created_at.isoformat()
        updated_at = (obj.updated_at or datetime.now()).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO industrial_knowledge_objects
                (object_id, object_type, name, canonical_name, description, project, origin_engine,
                 confidence, validated, version, created_at, updated_at, tags_json, payload_json, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    obj.object_id,
                    obj.object_type,
                    obj.name,
                    obj.canonical_name or obj.name,
                    obj.description,
                    obj.project,
                    obj.origin_engine,
                    obj.confidence,
                    1 if obj.validated else 0,
                    obj.version,
                    created_at,
                    updated_at,
                    json.dumps(obj.tags, ensure_ascii=False),
                    json.dumps(payload, ensure_ascii=False, default=str),
                    checksum,
                ),
            )
            conn.execute("DELETE FROM industrial_relationships WHERE source_object_id = ?", (obj.object_id,))
            for relation in obj.relationships:
                conn.execute(
                    """
                    INSERT INTO industrial_relationships (source_object_id, target_object_id, relation_type, metadata_json)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        obj.object_id,
                        relation.get('target_object_id') or relation.get('target_id') or relation.get('target') or '',
                        relation.get('relation_type') or relation.get('type') or 'related_to',
                        json.dumps(relation, ensure_ascii=False, default=str),
                    ),
                )

        self.save_knowledge(self._industrial_object_to_knowledge_item(obj))
        return obj.object_id

    def get_industrial_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM industrial_knowledge_objects WHERE object_id = ?",
                (object_id,),
            ).fetchone()
            if not row:
                return None
            result = dict(row)
            result['tags'] = json.loads(result.get('tags_json') or '[]')
            result['payload'] = json.loads(result.get('payload_json') or '{}')
            result['relationships'] = self.get_object_relationships(object_id)
            return result

    def list_industrial_objects(self, object_type: Optional[str] = None, project: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            sql = """
                SELECT object_id, object_type, name, canonical_name, description, project, origin_engine,
                       confidence, validated, version, created_at, updated_at, tags_json, checksum
                FROM industrial_knowledge_objects
                WHERE 1=1
            """
            params: list[Any] = []
            if object_type:
                sql += " AND object_type = ?"
                params.append(object_type)
            if project:
                sql += " AND project = ?"
                params.append(project)
            sql += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item['tags'] = json.loads(item.get('tags_json') or '[]')
                result.append(item)
            return result

    def search_industrial_objects(self, query: str, object_type: Optional[str] = None, project: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            sql = """
                SELECT object_id, object_type, name, canonical_name, description, project, origin_engine,
                       confidence, validated, version, created_at, updated_at, tags_json
                FROM industrial_knowledge_objects
                WHERE (name LIKE ? OR canonical_name LIKE ? OR description LIKE ? OR payload_json LIKE ?)
            """
            params: list[Any] = [f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%']
            if object_type:
                sql += " AND object_type = ?"
                params.append(object_type)
            if project:
                sql += " AND project = ?"
                params.append(project)
            sql += " ORDER BY confidence DESC, updated_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item['tags'] = json.loads(item.get('tags_json') or '[]')
                result.append(item)
            return result

    def get_object_relationships(self, object_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT source_object_id, target_object_id, relation_type, metadata_json FROM industrial_relationships WHERE source_object_id = ?",
                (object_id,),
            ).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item['metadata'] = json.loads(item.get('metadata_json') or '{}')
                result.append(item)
            return result

    def _industrial_object_to_knowledge_item(self, obj: IndustrialKnowledgeObject) -> KnowledgeItem:
        serialized_sections = [
            obj.description,
            json.dumps(obj.technical_data, ensure_ascii=False, default=str),
            json.dumps(obj.operational_data, ensure_ascii=False, default=str),
            json.dumps(obj.commercial_data, ensure_ascii=False, default=str),
            json.dumps(obj.kpis, ensure_ascii=False, default=str),
            json.dumps(obj.digital_twin_params, ensure_ascii=False, default=str),
            json.dumps(obj.simulation_params, ensure_ascii=False, default=str),
            json.dumps(obj.benchmark_data, ensure_ascii=False, default=str),
        ]
        return KnowledgeItem(
            id=obj.object_id,
            title=obj.name,
            category=obj.object_type,
            subcategory=obj.origin_engine,
            summary=obj.description[:500],
            content="\n".join(part for part in serialized_sections if part),
            sources=obj.source_refs,
            tags=obj.tags,
            entities=[{'type': 'object_type', 'value': obj.object_type}],
            relationships=obj.relationships,
            confidence=obj.confidence,
            validated=obj.validated,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            version=obj.version,
            project=obj.project,
        )
