from trl import DPOTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model
from datasets import load_dataset


MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"

# ---------- LOAD MODEL ----------
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# ---------- LOAD DATA ----------
dataset = load_dataset("json", data_files="data/preferences.json")

# ---------- PEFT CONFIG ----------
peft_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, peft_config)

# ---------- TRAINING ARGS ----------
training_args = TrainingArguments(
    output_dir="./dpo-model",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=5e-5,
    num_train_epochs=1,
    logging_steps=10,
    save_strategy="epoch",
    report_to="none"
)

# ---------- TRAINER ----------
trainer = DPOTrainer(
    model=model,
    ref_model=None,
    args=training_args,
    train_dataset=dataset["train"],
    tokenizer=tokenizer
)

# ---------- TRAIN ----------
trainer.train()
