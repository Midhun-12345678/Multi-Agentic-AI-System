from trl import DPOTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from datasets import load_dataset

model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")

dataset = load_dataset("json", data_files="data/preferences.json")

peft_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj","v_proj"],
    lora_dropout=0.05
)

model = get_peft_model(model, peft_config)

trainer = DPOTrainer(
    model=model,
    ref_model=None,
    args={"output_dir": "./dpo-model"},
    train_dataset=dataset["train"],
    tokenizer=tokenizer
)

trainer.train()
