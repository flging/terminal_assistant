import json
import os
from openai import OpenAI
import argparse

client = OpenAI(api_key="__________", base_url="https://api.upstage.ai/v1/solar")

def create_embedding(text):
    response = client.embeddings.create(
        model="solar-embedding-1-large-passage",
        input=text
    )
    return response.data[0].embedding

def update_RAG_DB(input_file='PureDB.json', output_file='RAG_DB.json'):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rag_db = []

    for item in data:
        description = item.get('description', '').strip()
        command = item.get('command', '').strip()
        examples = item.get('examples', [])

        if not description or not command:
            print(f"잘못된 입력 형식: {item}")
            continue

        full_text = f"설명: {description}\n명령어: {command}\n사용 예시:\n"
        for i, example in enumerate(examples, 1):
            full_text += f"{i}. {example}\n"

        embedding = create_embedding(full_text)

        rag_db.append({
            "description": description,
            "command": command,
            "examples": examples,
            "embedding": embedding
        })
        print(f"명령어 처리 완료: {command}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(rag_db, f, ensure_ascii=False, indent=2)

    print(f"RAG DB가 성공적으로 생성되었습니다. (파일: {output_file})")

def main():
    parser = argparse.ArgumentParser(description="PureDB.json을 RAG DB로 변환")
    parser.add_argument("--input", default="PureDB.json", help="입력 JSON 파일 경로 (기본값: PureDB.json)")
    parser.add_argument("--output", default="RAG_DB.json", help="출력 RAG DB 파일 경로 (기본값: RAG_DB.json)")
    args = parser.parse_args()

    update_RAG_DB(args.input, args.output)

if __name__ == "__main__":
    main()