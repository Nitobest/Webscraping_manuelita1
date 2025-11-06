"""
Sistema RAG: Retrieval-Augmented Generation

Integra búsqueda híbrida (vectorial + BM25) con re-ranking.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from langchain_community.document_loaders import DirectoryLoader, TextLoader
    from langchain_text_splitters import MarkdownHeaderTextSplitter
    from langchain_community.vectorstores import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.retrievers import BM25Retriever
    try:
        from langchain.retrievers import EnsembleRetriever, ContextualCompressionRetriever
    except ImportError:
        from langchain_community.retrievers import EnsembleRetriever
        from langchain.retrievers import ContextualCompressionRetriever
    try:
        from langchain_community.cross_encoders import HuggingFaceCrossEncoder
        from langchain.retrievers.document_compressors import CrossEncoderReranker
    except ImportError:
        HuggingFaceCrossEncoder = None
        CrossEncoderReranker = None
except ImportError as e:
    logger.error(f"Dependencias RAG no instaladas: {e}")
    EnsembleRetriever = None
    ContextualCompressionRetriever = None
    CrossEncoderReranker = None
    HuggingFaceCrossEncoder = None


class RAGSystem:
    """Sistema RAG con búsqueda híbrida y re-ranking."""
    
    def __init__(self, data_dir: str = "../data/raw/processed", 
                 vectordb_dir: str = "./vectordb",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Inicializa el sistema RAG.
        
        Args:
            data_dir: Directorio con archivos markdown
            vectordb_dir: Directorio para la base vectorial
            embedding_model: Modelo de embeddings
        """
        self.data_dir = data_dir
        self.vectordb_dir = vectordb_dir
        self.embedding_model_name = embedding_model
        self.vectorstore = None
        self.ensemble_retriever = None
        self.reranking_retriever = None
        self.documents = []
        self.splits = []
        
        self._initialize()
    
    def _initialize(self) -> None:
        """Inicializa componentes RAG."""
        try:
            logger.info("Inicializando sistema RAG...")
            
            # 1. Cargar documentos
            self._load_documents()
            
            # 2. Crear embeddings
            self._create_embeddings()
            
            # 3. Crear retriever híbrido
            self._create_hybrid_retriever()
            
            # 4. Crear re-ranker
            self._create_reranker()
            
            logger.info("✅ Sistema RAG inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando RAG: {e}")
    
    def _load_documents(self) -> None:
        """Carga documentos markdown."""
        try:
            loader = DirectoryLoader(
                path=self.data_dir,
                glob="**/*.md",
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"},
            )
            self.documents = loader.load()
            logger.info(f"✅ Cargados {len(self.documents)} documentos")
            
            # Dividir con MarkdownHeaderTextSplitter
            headers = [
                ("#", "Titulo1"),
                ("##", "Titulo2"),
                ("###", "Titulo3"),
            ]
            splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers,
                strip_headers=False
            )
            
            self.splits = []
            for doc in self.documents:
                chunks = splitter.split_text(doc.page_content)
                self.splits.extend(chunks)
            
            logger.info(f"✅ {len(self.splits)} chunks creados")
        except Exception as e:
            logger.error(f"Error cargando documentos: {e}")
            self.documents = []
            self.splits = []
    
    def _create_embeddings(self) -> None:
        """Crea base vectorial con embeddings."""
        try:
            if not self.splits:
                logger.warning("No hay splits para embeddings")
                return
            
            embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model_name
            )
            
            Path(self.vectordb_dir).mkdir(parents=True, exist_ok=True)
            
            self.vectorstore = Chroma.from_documents(
                documents=self.splits,
                embedding=embeddings,
                persist_directory=self.vectordb_dir
            )
            logger.info("✅ Base vectorial creada")
        except Exception as e:
            logger.error(f"Error creando embeddings: {e}")
    
    def _create_hybrid_retriever(self) -> None:
        """Crea retriever híbrido (vectorial + BM25)."""
        try:
            if not self.vectorstore or not self.splits:
                logger.warning("Vectorstore o splits no disponibles")
                return
            
            if not EnsembleRetriever:
                logger.warning("EnsembleRetriever no disponible, usando solo vectorstore")
                self.ensemble_retriever = self.vectorstore.as_retriever(search_kwargs={"k": 7})
                return
            
            # Semantic
            semantic_retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": 7}
            )
            
            # BM25
            keyword_retriever = BM25Retriever.from_documents(self.splits)
            keyword_retriever.k = 7
            
            # Ensemble
            self.ensemble_retriever = EnsembleRetriever(
                retrievers=[semantic_retriever, keyword_retriever],
                weights=[0.75, 0.25]
            )
            logger.info("✅ Retriever híbrido creado")
        except Exception as e:
            logger.error(f"Error creando hybrid retriever: {e}")
    
    def _create_reranker(self) -> None:
        """Crea re-ranker con Cross-Encoder."""
        try:
            if not self.ensemble_retriever:
                logger.warning("Ensemble retriever no disponible")
                return
            
            if not HuggingFaceCrossEncoder or not CrossEncoderReranker:
                logger.warning("HuggingFaceCrossEncoder no disponible, usando ensemble sin re-ranking")
                self.reranking_retriever = self.ensemble_retriever
                return
            
            reranker_model = HuggingFaceCrossEncoder(
                model_name="BAAI/bge-reranker-base"
            )
            compressor = CrossEncoderReranker(
                model=reranker_model,
                top_n=4
            )
            
            self.reranking_retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=self.ensemble_retriever
            )
            logger.info("✅ Re-ranker creado")
        except Exception as e:
            logger.error(f"Error creando reranker: {e}")
            # Fallback: usar ensemble sin re-ranking
            self.reranking_retriever = self.ensemble_retriever
    
    def retrieve(self, query: str, top_k: int = 4) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Recupera contexto para una query.
        
        Returns:
            (contexto_consolidado, documentos_recuperados)
        """
        try:
            if not self.reranking_retriever:
                logger.warning("Reranking retriever no disponible")
                return "", []
            
            docs = self.reranking_retriever.invoke(query)
            
            # Consolidar contexto
            context_parts = []
            doc_info = []
            
            for i, doc in enumerate(docs[:top_k]):
                context_parts.append(doc.page_content)
                doc_info.append({
                    'rank': i + 1,
                    'content': doc.page_content[:200],  # Preview
                    'source': doc.metadata.get('source', 'Unknown'),
                    'relevance': 'Alta' if i < 2 else 'Media'
                })
            
            consolidated_context = "\n---\n".join(context_parts)
            return consolidated_context, doc_info
        except Exception as e:
            logger.error(f"Error retrieving: {e}")
            return "", []
    
    def search(self, query: str, top_k: int = 4) -> Dict[str, Any]:
        """
        Búsqueda completa con contexto y metadatos.
        """
        context, docs = self.retrieve(query, top_k)
        
        return {
            'query': query,
            'context': context,
            'documents': docs,
            'total_docs_available': len(self.documents),
            'total_chunks': len(self.splits)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del sistema RAG."""
        return {
            'documents_loaded': len(self.documents),
            'chunks_created': len(self.splits),
            'embedding_model': self.embedding_model_name,
            'vectorstore_available': self.vectorstore is not None,
            'retriever_available': self.reranking_retriever is not None
        }


if __name__ == '__main__':
    # Ejemplo de uso
    rag = RAGSystem()
    result = rag.search("¿Cuál es la historia de Manuelita?")
    print(f"Contexto: {result['context'][:300]}...")
