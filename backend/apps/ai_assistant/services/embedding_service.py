class EmbeddingService:
    DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    _model = None
    _model_name = None

    @classmethod
    def get_model(cls, model_name=None):
        model_name = model_name or cls.DEFAULT_MODEL_NAME

        if cls._model is not None and cls._model_name == model_name:
            return cls._model

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required to generate embeddings."
            ) from exc

        cls._model = SentenceTransformer(model_name)
        cls._model_name = model_name
        return cls._model

    @classmethod
    def embed_texts(cls, texts, model_name=None):
        model_name = model_name or cls.DEFAULT_MODEL_NAME
        model = cls.get_model(model_name)

        embeddings = model.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embeddings.tolist()

    @classmethod
    def embed_query(cls, query, model_name=None):
        return cls.embed_texts([query], model_name=model_name)[0]
