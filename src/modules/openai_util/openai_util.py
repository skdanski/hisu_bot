import openai
from util import config
from util import logger as log

logger = log.Logger('openai_util', 'openai_util_logger')
configuration = config.Config()
openai.api_key = configuration.openai_api_key


def chat(prompt, max_token=2000, outputs=1):
    logger.info('chat', 'sending prompt to openai: ' + prompt)

    # using OpenAI's Completion module that helps execute 
    # any tasks involving text 
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are someone with a sophisticated and analytical mind especially when it comes to the arts."
                + " You constantly call Young Joon a capper and miss having your younger brother's Bert home cooked meals."},
            {"role": "user", "content": prompt}
        ],
        # generated output can have "max_tokens" number of tokens 
        max_tokens=max_token,
        # number of outputs generated in one call
        n=outputs,
        temperature=0.2

    )
    # creating a list to store all the outputs
    output = response.choices[0].message.content.strip()
    return output

def translate_text(text, source_language, target_language, max_token=2000, outputs=1):
    logger.info('translate_text', 'translating text from ' + source_language + ' to ' + target_language + ': ' + text)

    prompt = f"Translate the following '{source_language}' text to '{target_language}': {text}"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that purely translates text given to you."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_token,
        n=outputs,
        top_p=0.1
    )

    translation = response.choices[0].message.content.strip()
    return translation