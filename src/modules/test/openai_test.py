from openai_util import openai_util

prompt = """hi hisu, how was ur day?"""
print(prompt)
print(openai_util.chat(prompt))
print(openai_util.translate_text('hello', 'english', 'japanese'))