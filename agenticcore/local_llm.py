"""Local LLM using transformers (lightweight models)."""
import os
from typing import Dict, Any, Optional

_model = None
_tokenizer = None

def _load_model():
    """Load local LLM (lazy loading)."""
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        
        model_name = os.getenv("LOCAL_LLM_MODEL", "microsoft/phi-2")  # Small 2.7B model
        
        _tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        _model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            device_map="cpu",
            trust_remote_code=True
        )
        return _model, _tokenizer
    except Exception as e:
        return None, None

def generate_local(prompt: str, max_tokens: int = 100) -> Dict[str, Any]:
    """Generate text using local LLM."""
    model, tokenizer = _load_model()
    
    if model is None:
        return {"provider": "local", "text": "", "error": "Model not available"}
    
    try:
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove prompt from output
        text = text[len(prompt):].strip()
        return {"provider": "local", "text": text}
    except Exception as e:
        return {"provider": "local", "text": "", "error": str(e)}
