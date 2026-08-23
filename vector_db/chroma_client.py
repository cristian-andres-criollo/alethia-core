import json
import os

class ChromaMemoryClient:
    def __init__(self, persist_directory="./chroma_db"):
        """
        Inicializa una memoria simple basada en JSON (Reemplazo ligero de ChromaDB para evitar errores de C++ en Windows).
        """
        self.memory_file = os.path.join(persist_directory, "memory.json")
        os.makedirs(persist_directory, exist_ok=True)
        
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
        
        print(f"[Memoria Ligera] Inicializada en {self.memory_file}")

    def save_memory(self, memory_id: str, content: str, metadata: dict = None):
        """
        Guarda un nuevo recuerdo en el archivo JSON.
        """
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                memories = json.load(f)
            
            memories.append({
                "id": memory_id,
                "content": content,
                "metadata": metadata or {}
            })
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(memories, f, indent=4)
            return True
        except Exception as e:
            print(f"[Memoria Error] No se pudo guardar el recuerdo: {e}")
            return False

    def search_memories(self, query: str, n_results: int = 3):
        """
        Busca recuerdos que contengan palabras clave de la consulta.
        """
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                memories = json.load(f)
            
            if not memories:
                return "No se encontraron recuerdos relevantes."
            
            # Búsqueda súper básica por palabras (para no requerir librerías complejas)
            query_words = query.lower().split()
            scored_memories = []
            
            for mem in memories:
                score = sum(1 for word in query_words if word in mem["content"].lower())
                if score > 0:
                    scored_memories.append((score, mem["content"]))
            
            # Ordenar por los que tuvieron más coincidencias y tomar los top N
            scored_memories.sort(reverse=True, key=lambda x: x[0])
            top_memories = [m[1] for m in scored_memories[:n_results]]
            
            if not top_memories:
                return "No se encontraron recuerdos relevantes."
                
            return "\n---\n".join(top_memories)
        except Exception as e:
            print(f"[Memoria Error] Fallo al buscar: {e}")
            return "Error al consultar la memoria."
