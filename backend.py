# This file does article summarization automatically using another request to ChatGPT (gpt-3.5-turbo)
# Writes to a JSONL file called "marketSizing.jsonl" with only two properties "prompt" and "completion"
# "prompt" should contain the article text, and "completion" should contain the summary generated
# Uploads the data to OpenAI API
# Uses the data to train a model
# TODO: Fix the printing of the model analysis
# TODO: The dropdown menu connects to the number of articles uploaded from each category in the bar graphs
# at the bottom of the advisor's page. Add all articles into the same model though.

from flask import Flask, request, jsonify
import os
import openai
import json
from openai import OpenAI
from flask_cors import CORS
import logging
from pathlib import Path
import time

# Set up Flask
app = Flask(__name__)
CORS(app)
logger = logging.getLogger("mypackage.mymodule")  # or __name__ for current module
logger.setLevel(logging.ERROR)


################ For index-advisee ##################
@app.route('/api/research', methods=['POST'])
def research():
    print("Received a request to /api/research")

    # Ensure your OPENAI_API_KEY environment variable is set
    OPENAI_API_KEY =os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=OPENAI_API_KEY)

    # TODO: Make industry and topic based on the drop-down menu
    industry = "parking"
    topic = "market sizing"

    # Use a pre-trained OpenAI API call to do research across the web for this information
    query = "Please do research for me given that my app is in the " + industry + "what is the usual geographical location, age, gender and income of user of this type of app?"
    response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[
        {
          "role": "system",
          "content": "Please find correct market data across the web, based on other applications in the same industry. Data can be general (statistical) or specific to other existing applications. When referring to a general statistic, please provide the URL where the data was obtained. When referring to a specific application, list the application name and URL.  "

        },
        {
          "role": "user",
          "content": query
        }
      ],
      temperature=0.7,
      max_tokens=250,
      top_p=1
    )

    researchbyChatBot = response.choices[0].message.content
    print("Research is ready: ")
    print(researchbyChatBot)

    return jsonify(message=researchbyChatBot)


    
################ For index-advisor ##################
# Receive and handle the request to upload a new article
@app.route('/api/upload_summarize_train', methods=['POST'])
def upload_summarize_train():
    print("Received a request to /api/upload_summarize_train")
    # Ensure your OPENAI_API_KEY environment variable is set
    OPENAI_API_KEY =os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Extracting the text sent from the frontend
    data = request.json
    text_to_summarize = data['text']
    # print(f"Text to summarize: {text_to_summarize}")

    # Call OpenAI's API to summarize the text
    summary = openai_summarize_text(client, text_to_summarize)

    # print(f"Summary: {summary}")

    # Write to marketSizing.jsonl (adding to the data set)
    file_path = "topic_datasets_generated/marketSizing.jsonl"
    write_to_jsonl(file_path, text_to_summarize, summary)

    # Upload the data to be added as Training Data
    remote_openAI_file_id = upload_dataset(client, file_path)

    # Train the model
    fine_tuned_model = train_model(client, remote_openAI_file_id)

    # Check the fine-tuning status (Loop with a time delay)
    # Retrieve the fine-tuning job details
    status = client.fine_tuning.jobs.retrieve(fine_tuned_model.id).status
    if status not in ["succeeded", "failed"]:
        print(f"Job not in terminal status: {status}. Waiting.")
        while status not in ["succeeded", "failed"]:
            time.sleep(6)
            status = client.fine_tuning.jobs.retrieve(fine_tuned_model.id).status
            print(f"Status: {status}")

    if(status == "succeeded" ):
        print("--------- SUCCESS ---------")
        print(f"Finetune job {fine_tuned_model.id} finished with status: {status}")
        print("------------------")
        # Retrieve checkpoints
        checkpoints = retrieve_checkpoint_status(client, fine_tuned_model.id)
        # Analyze how well the model did
        # Print out the training loss, training token accuracy valid loss valid token accuracy
        retrieve_finetuning_metrics(client, fine_tuned_model.id)
    else:
        print(f"Finetune job {fine_tuned_model.id} finished with status: {status}")

    print("Checking other finetune jobs in the subscription.")
    all_trained_models = client.fine_tuning.jobs.list()
    print(f"Found {len(all_trained_models.data)} finetune jobs.")

    # Retrieve the finetuned model
    fine_tuned_model = all_trained_models.data[0].fine_tuned_model
    print("Fine tune model: ")
    print( fine_tuned_model)
    # TODO: Make industry and topic based on the drop-down menu
    industry = "parking"
    topic = "market sizing"
    if fine_tuned_model is None:
        print("Failed to train model.")
    else:
        print("Fine_tuned_model existed")
        # TODO: Make this based on the dropdown menu choice on Advisor Upload page

        msg_for_user_ret = use_trained_model_get_steps(client, industry, topic, fine_tuned_model)
        return jsonify(message=msg_for_user_ret.content)

    return "Fine tune model didn't exist"

# Send the Cubatorin answer back to the frontend
@app.route('/get_message')
def get_message():
    print("---------- Testing the model just trained. ----------")
    # Ensure your OPENAI_API_KEY environment variable is set
    OPENAI_API_KEY =os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=OPENAI_API_KEY)

    # TODO: Make industry and topic based on the drop-down menu
    industry = "parking"
    topic = "market sizing"

    print("Checking other finetune jobs in the subscription.")
    all_trained_models = client.fine_tuning.jobs.list()
    #print(all_trained_models)
    print(all_trained_models.data)
    print(f"--------Found at least {len(all_trained_models.data)} finetune jobs.----------")

    fine_tuned_model = all_trained_models.data[0].fine_tuned_model

    print(fine_tuned_model)

    if fine_tuned_model is None:
        print("Model not found")
    else:
        print("fine_tuned_model existed")

        # use_trained_model_get_steps returns the message
        chatCompletionMessage = use_trained_model_get_steps(client, industry, topic, fine_tuned_model)
        chatCompletionMsgContent = chatCompletionMessage.content
        return jsonify(message=chatCompletionMsgContent)

    return "Model not found"

def openai_summarize_text(client, text_to_summarize):
    # TODO: Explicitly asked for 3 TODO's in prompt, potentially allow for changes to this number
    response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[
        {
          "role": "system",
          "content": "Summarize content you are provided with for a university student in 3 sentences, being specific about the steps provided. Do not state that the article is about market sizing. Start and end the summary with specific steps. Break steps into bullet points instead of using commas for subtasks in each step. Start each step with a verb."

        },
        {
          "role": "user",
          "content": text_to_summarize
        }
      ],
      temperature=0.7,
      max_tokens=250,
      top_p=1
    )

    summaryByChatBot = response.choices[0].message.content
    print(summaryByChatBot)

    return summaryByChatBot


def write_to_jsonl(filename, article_text, summary):
    with open(filename, 'a') as f:  # Append to the jsonl file
        record = {
            "messages": [
                {
                    "role": "system",
                    "content": "Cubatorin is a factual chatbot helps new tech Entrepreneurs."
                },
                {
                    "role": "user",
                    "content": "I have just decided to build a new parking app, what steps do I take when performing market sizing?"
                },
                {
                    # TODO: Expert Knowledge: Get this from Rehber
                    "role": "assistant",
                    "content": summary
                }
            ]
        }

        f.write(json.dumps(record) + "\n")


def upload_dataset(client, local_file_path):
    try:
        # The 'file' parameter takes a path to the local file
        response = client.files.create(
            file=open(local_file_path, 'rb'),  # Open the file in binary read mode
            purpose="fine-tune",
        )
        print(f"---------File uploaded successfully with file ID:-------")
        print(response.id)
        return response.id
    except Exception as e:
        print(f"Failed to upload file: {e}")
        return None



def train_model(client, remote_openAI_file_id):
    try:
        fine_tuned_model = client.fine_tuning.jobs.create(
            model="gpt-3.5-turbo",
            training_file=remote_openAI_file_id,
        )

        # Consider changing the above to the commented part by ChatGPT
        # fine_tuned_model = client.fine_tuning.jobs.create(
        #    model="gpt-3.5-turbo",
        #    training_file=remote_openAI_file_id,
        #    compute_class="standard",  # You can adjust this based on your requirements
        #    n_epochs=4,  # Number of training epochs, adjust as necessary
        #    checkpoint_frequency=1  # Adjust frequency of checkpoints
        # )

        print("Model trained successfully with uploaded data")
        # print(fine_tuned_model)

        return fine_tuned_model  # Retrieve the name of the fine-tuned model
    except openai.APIConnectionError as e:
        print("The server could not be reached")
        print(e.__cause__)  # an underlying Exception, likely raised within httpx.
    except openai.RateLimitError as e:
        print("A 429 status code was received; we should back off a bit.")
    except openai.APIStatusError as e:
        print("Another non-200-range status code was received")
        print(e.status_code)
        print(e.response)
        print(e.response.text)  # Printing the detailed error message
        return None

def use_trained_model_get_steps(client, industry, topic, fine_tuned_model):
    query = "I have just decided to build a new" + industry + "app, what steps do I take when performing" + topic + "?"
    completion = client.chat.completions.create(
      model = fine_tuned_model,
      messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": query}
       ]
    )

    msg_for_user = completion.choices[0].message
    print(msg_for_user)
    return msg_for_user


def retrieve_checkpoint_status(client, fine_tuned_model_id):
    try:
        fine_tune_details = client.fine_tuning.jobs.retrieve(fine_tuned_model_id)
        print("------Retrieved checkpoints:--------")
        print(fine_tune_details)
        return fine_tune_details
    except Exception as e:
        print(f"Failed to retrieve checkpoints: {e}")
        return None


def retrieve_finetuning_metrics(client, fine_tuned_model_id):
    try:
        print("----Analyze the model: Print out the training loss, training token accuracy valid loss valid token accuracy-----")
")
        # Retrieve the fine-tuning job details
        job_details = client.fine_tuning.jobs.retrieve(fine_tuned_model_id)

        # Convert the job details to a dictionary
        job_details_dict = job_details.to_dict()

        # Extract metrics from the job details
        metrics = job_details_dict.get("result", {}).get("metrics", {})

        # Print out the fine-tuning job details
        print("Fine-tuning job details:")
        print(json.dumps(job_details, indent=2))

        # Print out the metrics specifically
        print("Metrics:")
        print(json.dumps(metrics, indent=2))

        return job_details
    except Exception as e:
        print(f"Failed to retrieve fine-tuning job details: {e}")
        return None


if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000, debug=True)

