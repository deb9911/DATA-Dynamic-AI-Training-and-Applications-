from transformers import AutoModelForSequenceClassification, AutoTokenizer, TrainingArguments, Trainer
from datasets import load_dataset


# Load the pre-trained model and tokenizer
model_name = "bert-base-uncased"
model = AutoModelForSequenceClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)


def llm_check():
    # Sample text to classify
    text = "This is not a positive sentence."

    # Tokenize the input
    inputs = tokenizer(text, return_tensors="pt")

    # Perform inference
    outputs = model(**inputs)
    logits = outputs.logits

    # Get predicted class ID
    predicted_class_id = logits.argmax().item()

    # Define labels (replace with your actual labels)
    labels = ["negative", "positive"]

    # Get predicted label
    predicted_label = labels[predicted_class_id]

    print(f"Predicted label for '{text}': {predicted_label}")


def load_training_dataset():
    # Load your dataset (replace with your actual dataset name)
    dataset = load_dataset("glue", "mrpc")
    print('\n~~~~\t:', dataset)

    # Tokenize the data
    def tokenize_function(examples):
        return tokenizer(examples["sentence1"], examples["sentence2"], padding="max_length", truncation=True)

    tokenized_datasets = dataset.map(tokenize_function, batched=True)

    return tokenized_datasets


def get_training_args():
    training_args = TrainingArguments(
        output_dir="./results",  # Output directory
        num_train_epochs=3,  # Number of training epochs
        per_device_train_batch_size=8,  # Batch size
        warmup_steps=500,  # Number of warmup steps for learning rate scheduler
        weight_decay=0.01,  # Strength of weight decay
        logging_dir="./logs",  # Directory for storing logs
        logging_steps=10,
    )

    return training_args


def build_trainer(tokenized_datasets, training_args):
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        resume_from_checkpoint=True,
        eval_dataset=tokenized_datasets["validation"],
    )

    return trainer


if __name__ == '__main__':
    tokenized_datasets = load_training_dataset()
    training_args = get_training_args()
    trainer = build_trainer(tokenized_datasets, training_args)

    trainer.train()
