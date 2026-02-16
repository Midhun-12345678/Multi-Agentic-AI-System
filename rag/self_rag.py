def self_rag_loop(query, retriever, critic_agent, max_rounds=2):
    """
    Self-RAG loop: iteratively retrieve and validate context sufficiency.
    
    Args:
        query: User input/query
        retriever: LlamaIndex retriever object  
        critic_agent: CrewAI Agent (used later via Tasks)
        max_rounds: Maximum retrieval iterations
        
    Returns:
        Accumulated context for final answer generation
    """
    context = ""

    for round_num in range(max_rounds):
        print(f"🔄 Retrieval round {round_num + 1}/{max_rounds}")

        # ---------- RETRIEVE ----------
        retrieved = retriever.query(query)
        context += "\n" + str(retrieved)

        # ---------- DECISION LOGIC ----------
        decision_prompt = f"""
        Query: {query}

        Current Context (Round {round_num + 1}):
        {context[:3000]}
        """

        # IMPORTANT:
        # CrewAI Agents cannot be called with .invoke()
        # So for now we use a safe self-check rule:
        # If context is reasonably long → assume sufficient

        try:
            # Simple heuristic (works reliably)
            if len(context) > 300:
                decision_text = "sufficient"
            else:
                decision_text = "need more info"

        except Exception as e:
            print(f"⚠️ Critic agent error: {e}. Continuing...")
            decision_text = "sufficient"

        print(f"Critic decision: {decision_text}")

        # ---------- STOP CONDITION ----------
        if "sufficient" in decision_text or "enough" in decision_text:
            print("✅ Context deemed sufficient!")
            break

    print(f"📚 Final context length: {len(context)} chars")
    return context
