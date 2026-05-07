from .faiss_store_service import FaissStoreService


class QAService:
    DEFAULT_MODEL = "llama3"
    FALLBACK_ANSWER = "I could not find this information in the uploaded document."

    SYSTEM_PROMPT = (
        "You are an AI document assistant. Answer only from the provided context. "
        f'If the answer is not present in the context, say: "{FALLBACK_ANSWER}" '
        "Do not invent information. Keep the answer clear and concise."
    )

    @classmethod
    def answer_question(cls, document, question, top_k=5):
        if not question or not question.strip():
            raise ValueError("Question is required.")

        search_results = FaissStoreService.search_document(
            document=document,
            query=question,
            top_k=top_k,
        )

        citations = cls._build_citations(search_results)
        context = cls._build_context(citations)

        if not context:
            return {
                "answer": cls.FALLBACK_ANSWER,
                "citations": [],
            }

        prompt = cls._build_prompt(question=question, context=context)
        answer = cls._call_ollama(prompt)

        return {
            "answer": answer.strip() or cls.FALLBACK_ANSWER,
            "citations": citations,
        }

    @classmethod
    def _call_ollama(cls, prompt):
        try:
            from langchain_ollama import OllamaLLM
        except ImportError:
            try:
                from langchain_community.llms import Ollama
            except ImportError as exc:
                raise RuntimeError(
                    "LangChain Ollama integration is not installed. "
                    "Install langchain, langchain-community, and langchain-ollama."
                ) from exc

            llm = Ollama(model=cls.DEFAULT_MODEL)
        else:
            llm = OllamaLLM(model=cls.DEFAULT_MODEL)

        try:
            return llm.invoke(prompt)
        except Exception as exc:
            raise RuntimeError(
                "Ollama server or llama3 model is not available. "
                "Make sure Ollama is running and run: ollama pull llama3"
            ) from exc

    @staticmethod
    def _build_citations(search_results):
        citations = []

        for result in search_results:
            chunk = result["chunk"]
            citations.append(
                {
                    "chunk_id": str(chunk.id),
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "text": chunk.text,
                    "score": result["score"],
                }
            )

        return citations

    @staticmethod
    def _build_context(citations):
        context_parts = []

        for citation in citations:
            source_label = (
                f"chunk_id={citation['chunk_id']}; "
                f"chunk_index={citation['chunk_index']}; "
                f"page_number={citation['page_number']}"
            )
            context_parts.append(f"[{source_label}]\n{citation['text']}")

        return "\n\n---\n\n".join(context_parts)

    @classmethod
    def _build_prompt(cls, question, context):
        return (
            f"{cls.SYSTEM_PROMPT}\n\n"
            "Context:\n"
            f"{context}\n\n"
            "Question:\n"
            f"{question}\n\n"
            "Answer:"
        )
