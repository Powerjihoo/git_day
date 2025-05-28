import os, random, sys, copy
from typing import List
from pathlib import Path

import fire, setproctitle
import torch
import transformers
from accelerate import Accelerator

from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset, load_from_disk, concatenate_datasets

accelerator = Accelerator()

def train(
    # model/data params
    base_model: str = "meta-llama/Llama-3.2-1B",  # the only required argument
    output_dir: str = "./checkpoint",
    vram_available: str = None,
    # training hyperparams
    per_device_train_batch_size: int = 0,
    gradient_accumulation_steps: int = 0,
    num_epochs: int = 10,
    learning_rate: float = 3e-4,
    cutoff_len: int = 3076,
    warmup_ratio: float = 0.0,
    warmup_steps: int = 0,
    logging_steps: int = 1,
    eval_steps: int = 200,
    save_steps: int = 200,
    save_total_limit: int=3,
    lr_scheduler_type: str = 'cosine',
    # llm hyperparams
    add_eos_token: bool = False,
    # wandb params
    wandb_project: str = "",
    wandb_run_name: str = "",
    wandb_watch: str = "",  # options: false | gradients | all
    wandb_log_model: str = "",  # options: false | true
    resume_from_checkpoint: str = None,  # either training checkpoint or final adapter
    bf16: bool = False,
    data_path:str='./dataset/training.jsonl',
):
    """
    언어 모델을 학습합니다.

    이 함수는 Hugging Face Transformers 라이브러리와 Accelerate 라이브러리를 활용하여
    주어진 하이퍼파라미터와 설정에 따라 언어 모델을 미세 조정합니다. 모델은 제공된
    데이터셋으로 미세 조정되며, 실험 추적을 위한 로그, 체크포인트 저장, Weights & Biases 사용
    등의 옵션을 제공합니다.

    Args:
    ----------
    base_model : str
        미세 조정할 기본 모델의 경로입니다. 
    output_dir : str
        체크포인트와 학습된 모델이 저장될 디렉토리입니다.
    vram_available : str
        사용 가능한 VRAM의 양을 지정합니다. 
    per_device_train_batch_size : int
        장치(GPU/TPU 코어)당 훈련 배치 크기입니다.
    gradient_accumulation_steps : int
        모델 파라미터를 업데이트하기 전까지 그래디언트를 누적할 스텝 수입니다.
    num_epochs : int
        총 훈련 epoch 수입니다.
    learning_rate : float
        옵티마이저의 학습률입니다.
    cutoff_len : int
        토크나이제이션 시 최대 시퀀스 길이입니다.
    warmup_ratio : float
        학습률 워밍업에 사용할 총 훈련 스텝의 비율입니다.
    warmup_steps : int
        학습률 워밍업에 사용하는 스텝 수입니다.
    logging_steps : int
        로그 업데이트 간의 스텝 수입니다.
    eval_steps : int
        평가 간의 업데이트 스텝 수입니다.
    save_steps : int
        체크포인트 저장 간의 업데이트 스텝 수입니다.
    save_total_limit : int
        유지할 수 있는 최대 체크포인트 수입니다.
    lr_scheduler_type : str
        사용할 학습률 스케줄러의 유형입니다 (예: 'cosine').
    add_eos_token : bool
        토크나이제이션 시 시퀀스 종료 토큰을 추가할지 여부입니다.
    wandb_project : str
        Weights & Biases 프로젝트 이름입니다.
    wandb_run_name : str
        Weights & Biases의 실행 이름입니다.
    wandb_watch : str
        Weights & Biases 감시 옵션: 'false', 'gradients', 'all'.
    wandb_log_model : str
        Weights & Biases에서 모델을 로그할지 여부: 'false', 'true'.
    resume_from_checkpoint : str
        체크포인트 경로에서 훈련을 재개할 때 사용합니다.
    bf16 : bool
        bfloat16 정밀도 훈련을 사용할지 여부입니다.
    data_path : str
        JSONL 형식의 훈련 데이터셋 경로입니다.
    """
    
    
    setproctitle.setproctitle(f"{output_dir.split('/')[-1]}")
    
    if accelerator.is_main_process:
        print(type(add_eos_token))
    if int(os.environ.get("LOCAL_RANK", 0)) == 0:
        print(
            f"Training GAON LLM with params:\n"
            f"{vram_available=}\n"
            f"base_model: {base_model}\n"
            f"output_dir: {output_dir}\n"
            f"per_device_train_batch_size: {per_device_train_batch_size}\n"
            f"gradient_accumulation_steps: {gradient_accumulation_steps}\n"
            f"num_epochs: {num_epochs}\n"
            f"learning_rate: {learning_rate}\n"
            f"cutoff_len: {cutoff_len}\n"
            f"add_eos_token: {add_eos_token}\n"
            f"wandb_project: {wandb_project}\n"
            f"wandb_run_name: {wandb_run_name}\n"
            f"wandb_watch: {wandb_watch}\n"
            f"wandb_log_model: {wandb_log_model}\n"
            f"resume_from_checkpoint: {resume_from_checkpoint or False}\n"
        )
    assert base_model, "Please specify a --base_model, e.g. --base_model='huggyllama/llama-7b'"
    # gradient_accumulation_steps = batch_size // micro_batch_size

    # Check if parameter passed or if set within environ
    if accelerator.is_main_process:
        print(f"{wandb_project=}")
    use_wandb = len(wandb_project) > 0 or ("WANDB_PROJECT" in os.environ and len(os.environ["WANDB_PROJECT"]) > 0)
    # Only overwrite environ if wandb param passed
    if len(wandb_project) > 0:
        os.environ["WANDB_PROJECT"] = wandb_project
    if len(wandb_watch) > 0:
        os.environ["WANDB_WATCH"] = wandb_watch
    if len(wandb_log_model) > 0:
        os.environ["WANDB_LOG_MODEL"] = wandb_log_model
    if accelerator.is_main_process:
        print(f"{use_wandb=}")
    use_wandb = False  # TODO for debug

    
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype = torch.bfloat16 if bf16 else torch.float16,
        low_cpu_mem_usage=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    tokenizer.padding_side = "left"  # Allow batched inference

    def tokenize(prompt, add_eos_token=True):
        result = tokenizer(
            prompt,
            truncation=True,
            max_length=cutoff_len,
            padding=False,
            return_tensors=None,
        )
        if (
            result["input_ids"][-1] != tokenizer.eos_token_id
            and len(result["input_ids"]) < cutoff_len
            and add_eos_token
        ):
            result["input_ids"].append(tokenizer.eos_token_id)
            result["attention_mask"].append(1)

        result["labels"] = result["input_ids"].copy()

        return result

    def generate_and_tokenize(data_point, chat_template=True):
        
        inp=data_point['query']
        out=data_point['output']
        
        if chat_template:
            chat = [{f"role": "user", "content":inp},]
            inp = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
            
        all_text =f'{inp}{out}'        
        random_eos_token = add_eos_token
        tokenized_all_text = tokenize(all_text, add_eos_token=random_eos_token)
        
        tokenized_input = tokenize(inp, add_eos_token=random_eos_token)
        input_len = len(tokenized_input["input_ids"])-1

        tokenized_all_text["labels"] = [-100] * input_len + tokenized_all_text["labels"][input_len:]  
            
        return tokenized_all_text
    
    
    if vram_available == "48GB":
        ds_config_file = "ds_config/experimenting_a6000_nooffload_bf16.json"
        
    else:
        raise NotImplementedError

    cache_file_train = "./cache/train"
    cache_file_val = "./cache/val"
    
    with accelerator.main_process_first():

        data = load_dataset(
            'json',data_files={
                'train':os.path.join(data_path),
            }
        )
        
        total=data['train'].train_test_split(test_size=0.2, shuffle=True, seed=42)
        
        if not os.path.isdir(cache_file_train) or not os.path.isdir(cache_file_val):
            if accelerator.is_main_process:
                print("## Preprocessing Dataset")
            train_data = total['train'].map(generate_and_tokenize).shuffle()
            valid_data = total['test'].map(generate_and_tokenize).shuffle()
            
            train_data.save_to_disk(cache_file_train)
            valid_data.save_to_disk(cache_file_val)
        else:
            if accelerator.is_main_process:
                print("## Load From Disk")
            # 캐시 파일에서 데이터 불러옴
            train_data = load_from_disk(cache_file_train)
            valid_data = load_from_disk(cache_file_val)
    
    if accelerator.is_main_process:
        print("---")
        print(f'data form:{train_data}')
        print(f'data form:{valid_data}')
        print("---")


    trainer = transformers.Trainer(
        model=model,
        train_dataset=train_data,
        eval_dataset=valid_data,
        tokenizer=tokenizer,
        args=transformers.TrainingArguments(
            per_device_train_batch_size=per_device_train_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            per_device_eval_batch_size=1,
            warmup_steps=warmup_steps,
            # warmup_ratio=warmup_ratio,
            num_train_epochs=num_epochs,
            learning_rate=learning_rate,
            #lr_scheduler_type="cosine_with_restarts",
            logging_steps=logging_steps,
            #optim="adamw_torch",  # since we use DS optim?
            evaluation_strategy="steps", 
            save_strategy="steps",
            eval_steps=eval_steps,
            save_steps=save_steps,
            output_dir=output_dir,
            save_total_limit=save_total_limit,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            # ddp_find_unused_parameters=False if ddp else None,
            # ddp_find_unused_parameters=True,
            report_to="wandb",
            run_name=wandb_run_name if use_wandb else None,
            fp16=not bf16,
            bf16=bf16,
            gradient_checkpointing=True,
            deepspeed=ds_config_file,
        ),
        data_collator=transformers.DataCollatorForSeq2Seq(
            tokenizer, pad_to_multiple_of=4, return_tensors="pt", padding=True
        ),
    )
    model.config.use_cache = False

    trainer.train(resume_from_checkpoint=resume_from_checkpoint)

    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    if accelerator.is_main_process:
        print("\n If there's a warning about missing keys above, please disregard :)")


if __name__ == "__main__":
    fire.Fire(train)
    