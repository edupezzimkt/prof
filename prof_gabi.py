# pip install --upgrade wheel
from io import BytesIO
from pathlib import Path

import speech_recognition as sr
from playsound import playsound

import openai
import os
from dotenv import load_dotenv, find_dotenv

api_key = os.getenv('OPENAI_API_KEY')
client = openai.Client(api_key=api_key)

ARQUIVO_AUDIO = 'fala_assistant.mp3'

recognizer = sr.Recognizer()


# Prompt para direcionar as respostas
prompt_inicial = "Você é professor do nono ano de escola e vai ajudar a Gabriela a estudar as matérias, você se chama Profe Jubiscreuda. E vai responder do forma curta para não gastar muitos tokens" 


def grava_audio():
    with sr.Microphone() as source:
        print('Ouvindo...')
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)
    return audio

def transcricao_audio(audio):
    wav_data = BytesIO(audio.get_wav_data())
    wav_data.name = 'audio.wav'
    transcricao = client.audio.transcriptions.create(
        model='whisper-1',
        file=wav_data,
    )
    return transcricao.text

def completa_texto(mensagens):
    resposta = client.chat.completions.create(
        messages=mensagens,
        model='gpt-4o-mini', #gpt-3.5-turbo-0125
        max_tokens=1000,
        temperature=0
    )
    return resposta

def cria_3(texto):
    if Path(ARQUIVO_AUDIO).exists():
        Path(ARQUIVO_AUDIO).unlink()
    resposta = client.audio.speech.create(
        model='tts-1',
        voice='nova',
        input=texto
    )
    resposta.write_to_file(ARQUIVO_AUDIO)

def roda_audio():
    playsound(ARQUIVO_AUDIO)


if __name__ == '__main__':

    mensagens = [{'role': 'system', 'content': prompt_inicial}]

    while True:
        audio = grava_audio()
        transcricao = transcricao_audio(audio)
        mensagens.append({'role': 'user', 'content': transcricao})
        print(f'User: {mensagens[-1]["content"]}')
        resposta = completa_texto(mensagens)
        mensagens.append({'role': 'assistant', 'content': resposta.choices[0].message.content})
        print(f'Assistant: {mensagens[-1]["content"]}')
        cria_3(mensagens[-1]["content"])
        roda_audio()

