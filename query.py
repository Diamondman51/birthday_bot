from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

def generate(text):
    client = genai.Client(
        api_key=os.getenv('GEMINI_API'),
    )

    model = "gemini-2.5-flash-preview-05-20"
    contents = []
    query = types.Content(
        role='user',
        parts=[
            types.Part.from_text(text=text)
        ]
    )
    contents.append(query)
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
    )

    re = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    return re.text
        

if __name__ == "__main__":
    print(generate('Пожалуйста напиши только один образец поздравления на день рождение Ахмед от имени @Жавохир, не менее на 100 слов, не забудь добавить собачку перед именем поздравителя, пусть в ответе будет только само поздравление без никаких дополнительных ответов'))


# if __name__ == "__main__":


