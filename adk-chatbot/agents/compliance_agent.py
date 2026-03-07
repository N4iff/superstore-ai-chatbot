"""
Compliance Agent - RAG-based agent for SDAIA AI regulations
Returns structured answers for validation by rag_validator_agent
"""
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from config.settings import MODEL_NAME, OPENAI_API_KEY
import chromadb
import openai

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY


def create_compliance_agent() -> LlmAgent:
    """Create Compliance agent with RAG and automatic PDF highlighting"""

    def ask_sdaia(question: str) -> str:
        """
        Answer questions about SDAIA AI principles using RAG
        
        Args:
            question: User's question about SDAIA regulations
            
        Returns:
            Structured response with question, context, and answer
        """
        # Lazily initialize Chroma so the web server can boot even if the local
        # persisted DB is missing/corrupted (Chroma can panic in its Rust layer).
        try:
            client = chromadb.PersistentClient(path="data/chroma_db")
            collection = client.get_collection(name="sdaia_ai_principles")
        except Exception as e:
            # Keep the failure visible, but return a usable response instead of
            # crashing the whole process.
            return f"""VALIDATION_FORMAT:
QUESTION: {question}
CONTEXT: (Vector DB unavailable: {type(e).__name__}: {e})
ANSWER: لم أتمكن من الوصول إلى قاعدة بيانات المتجهات. شغّل `python scripts/create_vector_db.py` لإنشائها/إعادة إنشائها ثم أعد المحاولة."""

        # Create query embedding
        response = openai.embeddings.create(
            input=[question],
            model="text-embedding-3-small"
        )
        query_embedding = response.data[0].embedding
        
        # Search vector database
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        
        # Extract results
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        
        # Build context with citations
        context_str = ""
        for i, (doc, meta) in enumerate(zip(documents, metadatas), 1):
            context_str += f"[المصدر {i} - صفحة {meta['page']}]:\n{doc}\n\n"
        
        # Use LLM to generate answer
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """أنت خبير في مبادئ أخلاقيات الذكاء الاصطناعي وفقاً لسدايا.

أجب على السؤال بناءً على السياق المُعطى بطريقة واضحة ومفيدة:
1. اشرح المبادئ والمفاهيم بأسلوب مفهوم ومنظم
2. استشهد بأرقام الصفحات بعد كل نقطة: (صفحة X)
3. رتّب النقاط بأرقام (1، 2، 3...)
4. يمكنك تلخيص وشرح المحتوى بأسلوبك الخاص مع الحفاظ على الدقة
5. إذا لم يكن السياق كافياً، قل: "لم أجد معلومات كافية في الوثيقة"
6. أضف شرحاً أو توضيحاً عند الحاجة لجعل الإجابة أكثر فائدة"""},
                {"role": "user", "content": f"السؤال: {question}\n\nالسياق:\n{context_str}\n\nالإجابة:"}
            ],
            temperature=0.3
        )
        
        answer = completion.choices[0].message.content

        # Return structured format (PDF highlighting is triggered later by the parent agent)
        return f"""VALIDATION_FORMAT:
QUESTION: {question}
CONTEXT: {context_str}
ANSWER: {answer}"""
    
    sdaia_tool = FunctionTool(func=ask_sdaia)
    
    instruction = """
You are a SDAIA AI Ethics Compliance agent.

Your ONLY job: call ask_sdaia with the user's question and return the FULL result exactly as-is.

Workflow:
1. Call ask_sdaia(question=<user's question>)
2. Return the ENTIRE response you get back — do NOT modify, summarize, or reformat it.

The response will look like:
```
VALIDATION_FORMAT:
QUESTION: ...
CONTEXT: ...
ANSWER: ...
```

Return ALL of it. The parent agent handles validation and PDF creation.
"""
    
    return LlmAgent(
        name="compliance_agent",
        model=LiteLlm(model=MODEL_NAME),
        instruction=instruction,
        tools=[sdaia_tool],
        description="Answers SDAIA AI ethics questions using RAG over the SDAIA principles document."
    )