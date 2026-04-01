import os
import json
import logging
from pathlib import Path
from typing import List
import polars as pl
import numpy as np

try:
    import faiss
    from sentence_transformers import SentenceTransformer
except ImportError:
    logging.warning("No se detectó faiss ni sentence-transformers en el entorno")
logger = logging.getLogger(__name__)

# rutas por defecto para persistencia y lectura
GOLD_PATH = "data/curated/candidates_gold.parquet"
FAISS_INDEX_PATH = "data/curated/faiss_index.bin"
MAPPING_PATH = "data/curated/vector_mapping.json"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

def build_government_plans_index(
    gold_path: str = GOLD_PATH,
    index_path: str = FAISS_INDEX_PATH,
    mapping_path: str = MAPPING_PATH,
    model_name: str = MODEL_NAME
) -> None:
    logger.info(f"iniciando indexación offline desde {gold_path}")
    
    if not os.path.exists(gold_path):
        logger.error(f"no se encontró la capa gold: {gold_path}")
        return

    # filtramos los registros que realmente tengan contexto
    df = pl.read_parquet(gold_path).filter(
        pl.col("search_context").is_not_null() & (pl.col("search_context") != "")
    )
    
    if df.is_empty():
        logger.warning("No hay registros con search_context para procesar")
        return

    global_ids = df["global_id"].to_list()
    texts = df["search_context"].to_list()
    
    logger.info(f"Cargando modelo: {model_name}")
    model = SentenceTransformer(model_name)
    
    logger.info(f"Generando embeddings para {len(texts)} candidatos")
    # se requiere normalizar a 1 si queremos que el inner product
    # equivalga a cosine similarity
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    embeddings = np.array(embeddings, dtype=np.float32)
    dimension = embeddings.shape[1]
    
    logger.info(f"Construyendo indexflatip para dimension {dimension}")
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    
    Path(index_path).parent.mkdir(parents=True, exist_ok=True)
    
    faiss.write_index(index, index_path)
    logger.info(f"Índice persistido correctamente en: {index_path}")
    
    # el offset de faiss equivale a la posición en el array global_ids
    mapping = {i: str(gid) for i, gid in enumerate(global_ids)}
    with open(mapping_path, "w", encoding="utf-8") as file_map:
        json.dump(mapping, file_map, ensure_ascii=False, indent=2)
        
    logger.info(f"Mapeo serializado en {mapping_path}")


class SemanticSearch:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SemanticSearch, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self, 
        index_path: str = FAISS_INDEX_PATH, 
        mapping_path: str = MAPPING_PATH, 
        model_name: str = MODEL_NAME
    ):
        if getattr(self, "_initialized", False) and self.index_path == index_path:
            return
            
        self.index_path = index_path
        self.mapping_path = mapping_path
        self.model_name = model_name
        
        self.model = None
        self.index = None
        self.mapping = None
        
        self._initialized = True

    def initialize(self):
        if self.model is not None:
            return

        logger.info(f"Inicializando motor semántico local: {self.model_name}")      
        if not os.path.exists(self.index_path) or not os.path.exists(self.mapping_path):
            raise FileNotFoundError("No hay index válido; ejecutar build_government_plans_index() primero")

        self.index = faiss.read_index(self.index_path)

        with open(self.mapping_path, "r", encoding="utf-8") as mapping_file:
            str_mapping = json.load(mapping_file)
            self.mapping = {int(k): v for k, v in str_mapping.items()}

        self.model = SentenceTransformer(self.model_name)
        logger.info("Motor semántico cargado")

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        if self.model is None or self.index is None:
            self.initialize()
            
        logger.debug(f"Procesando query semántica: {query}")
        query_embedding = self.model.encode([query], normalize_embeddings=True)
        query_embedding = np.array(query_embedding, dtype=np.float32)
        scores, faiss_ids = self.index.search(query_embedding, top_k)
        
        results = []
        for rank in range(top_k):
            fid = faiss_ids[0][rank]
            score = scores[0][rank]
            if fid != -1 and fid in self.mapping:
                results.append({
                    "global_id": self.mapping[fid],
                    "score": float(score) 
                })
                
        return results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # script de prueba
    mock_gold = Path("data/curated/candidates_gold_mock.parquet")
    if not mock_gold.exists():
        logger.info("Creando mock dataset parquet para simulación")
        mock_gold.parent.mkdir(parents=True, exist_ok=True)
        df_mock = pl.DataFrame({
            "global_id": ["uuid-001", "uuid-002", "uuid-003", "uuid-004"],
            "search_context": [
                "reforma agraria integral, bonos sociales para el agro y tecnología hidroeléctrica de gran capacidad.",
                "apoyo condicionado y subsidios, lucha frontal contra el terrorismo y delincuencia en el callao",
                "inversión en el sistema de salud universal, construcción de hospitales modernos y programas de prevención.",
                "cero tolerancia a la corrupción, modernización digital de las entidades estatales y transparencia de código."
            ]
        })
        df_mock.write_parquet(mock_gold)
    
    # probar indexador
    build_government_plans_index(
        gold_path=str(mock_gold), 
        index_path="data/curated/faiss_index_test.bin", 
        mapping_path="data/curated/vector_mapping_test.json"
    )
    
    # verificar singleton
    search1 = SemanticSearch(
        index_path="data/curated/faiss_index_test.bin", 
        mapping_path="data/curated/vector_mapping_test.json"
    )
    search2 = SemanticSearch(
        index_path="data/curated/faiss_index_test.bin", 
        mapping_path="data/curated/vector_mapping_test.json"
    )
    
    print(f"¿Singleton es persistente entre instancias? -> {search1 is search2}")
    
    # verificar query
    query = "lucha contra la pobreza y ayuda gubernamental rápida"
    print(f"\nResultados del query '{query}':")
    resultados = search1.search(query, top_k=2)
    for res in resultados:
        print(f"Candidato (ID): {res['global_id']} | Afinidad Cosine Simm: {res['score']:.4f}")