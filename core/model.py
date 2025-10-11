# core/model.py
import re, os
from transformers import pipeline, StoppingCriteria, StoppingCriteriaList

MODEL_NAME = os.getenv("HF_MODEL_GENERATION", "distilgpt2")
_pipe = None

class StopOnMarkers(StoppingCriteria):
    def __init__(self, tokenizer, stop_strs=("\nUser:", "\nSystem:", "\n###", "\nProducts:", "\nVenue rules:", "\nParking rules:")):
        self.tokenizer = tokenizer
        self.stop_ids = [tokenizer(s, add_special_tokens=False).input_ids for s in stop_strs]

    def __call__(self, input_ids, scores, **kwargs):
        # stop if any marker sequence just appeared at the end
        for seq in self.stop_ids:
            L = len(seq)
            if L and len(input_ids[0]) >= L and input_ids[0][-L:].tolist() == seq:
                return True
        return False

def _get_pipe():
    global _pipe
    if _pipe is None:
        _pipe = pipeline("text-generation", model=MODEL_NAME)
    return _pipe

def model_generate(prompt, max_new_tokens=96, temperature=0.7, top_p=0.9):
    pipe = _get_pipe()
    tok = pipe.tokenizer

    stop = StoppingCriteriaList([StopOnMarkers(tok)])

    out = pipe(
        prompt,
        max_new_tokens=int(max_new_tokens),
        do_sample=True,
        temperature=float(temperature),
        top_p=float(top_p),
        repetition_penalty=1.15,          # discourages exact loops
        no_repeat_ngram_size=3,           # blocks short repeats like "Account/Account"
        pad_token_id=tok.eos_token_id or 50256,
        eos_token_id=tok.eos_token_id,    # stop at EOS if model supports
        stopping_criteria=stop,
    )
    return out[0]["generated_text"]
