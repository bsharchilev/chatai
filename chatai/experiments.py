import wandb
import time
import openai
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class DatasetParams:
    existing_dataset_id: Optional[str]


@dataclass
class ExperimentConfig:
    project_id: str
    experiment_id: str
    train_dataset: DatasetParams
    test_dataset: DatasetParams


class OpenAIExperiments:
    def __init__(self, openai_client: openai.OpenAI, wandb_api_key: str):
        self._openai_client = openai_client
        wandb.login(key=wandb_api_key)

    def run_experiment(self, config: ExperimentConfig):
        # query if datasets already exist, otherwise create them with given parameters
        # if needed - upload
        train_dataset_id = self._retrieve_or_generate_dataset(config.train_dataset, config)

        # submit fine-tuning job, use wandb native integration
        fine_tune_job_id = self._submit_fine_tune(train_dataset_id, config)

        # periodically poll status, and log train/test metrics
        result = self._wait_for_fine_tune(fine_tune_job_id)


        # once fine tune is done - query predictions on the test dataset:
          # take each conversation, do it step-by-step:
          # include a system message in each
          # include all user and assistant messages up to this point
          # generate new response, upload to W&B

        val_dataset_id = self._retrieve_or_generate_dataset(config.test_dataset, config)
        self._generate_test_predictions(val_dataset_id, result.fine_tuned_model)

    def _retrieve_or_generate_dataset(self, dataset_params: DatasetParams, config: ExperimentConfig) -> str:
        if dataset_params.existing_dataset_id is not None and self._dataset_exists(dataset_params.existing_dataset_id):
            dataset_id = dataset_params.existing_dataset_id
        else:
            dataset_path = self._create_and_save_dataset(config)
            dataset_id = self._upload_dataset(dataset_path)
        return dataset_id

    def _dataset_exists(self, dataset_id: str) -> bool:
        pass

    def _create_and_save_dataset(self, config: ExperimentConfig) -> str:
        pass

    def _upload_dataset(self, dataset_path: str) -> str:
        with open(dataset_path, 'rb') as file_to_upload:
            response = self._openai_client.files.create(
                file=file_to_upload,
                purpose="fine-tune",
            )
        return response.id

    def _submit_fine_tune(self, dataset_id: str, config: ExperimentConfig) -> str:
        response = self._openai_client.fine_tuning.jobs.create(
            training_file=dataset_id,
            model="gpt-4o-mini",
            hyperparameters={
                "n_epochs": 3,
            },
            integrations=[{
                "type": "wandb",
                "wandb": {
                    "project": config.project_id,
                    "name": config.experiment_id,
                }
            }],
        )

        fine_tune_id = response['id']
        print(f"Fine-tuning job submitted: {fine_tune_id}")

        return fine_tune_id

    def _wait_for_fine_tune(self, fine_tune_id: str):
        while True:
            # Retrieve the fine-tune status
            status = self._openai_client.fine_tuning.jobs.retrieve(fine_tune_id)
            # Log current status to W&B
            wandb.log({
                "status": status['status'],
            })

            print(f"Fine-tuning status: {status['status']}")

            if status['status'] in ["succeeded", "failed"]:
                break

            time.sleep(1 * 60 * 60)

        return status

    def _generate_test_predictions(self, dataset_id: str, model_id: str):
        print("Generating predictions for validation dataset: %s", dataset_id)

        try:
            # Load the validation dataset
            validation_data = list(self._openai_client.files.content(dataset_id).iter_lines())

            # Initialize completions list
            completions = []

            # Retrieve the fine-tuned model ID
            for example in validation_data:
                conversation_history = example["messages"]  # Chat history (system, user, assistant messages)
                true_completion = example["completion"]  # The expected final response


                # Call the OpenAI API to generate the assistant's next response
                response = self._openai_client.chat.completions.create(
                    model=model_id,
                    messages=conversation_history,  # Entire conversation history up to the point of prediction
                    max_tokens=150,
                    temperature=0.7
                )

                # Extract the generated assistant message from the response
                generated_message = response['choices'][0]['message']['content'].strip()

                # Append the assistant's generated message to the conversation history
                conversation_history.append({"role": "assistant", "content": generated_message})

                # Store the generated completion, true completion, and conversation history
                completions.append({
                    "conversation_history": conversation_history,
                    "true_completion": true_completion,
                    "generated_completion": generated_message
                })

                # Log the completion to W&B
                wandb.log({
                    "conversation_history": conversation_history,
                    "true_completion": true_completion,
                    "generated_completion": generated_message
                })
        except Exception as e:
            print("Error generating chat test predictions: %s", str(e))
