"""Claude API の薄いラッパー。JSON生成(構造化出力)と長文生成(ストリーミング)。"""

import json

import anthropic


class ClaudeClient:
    def __init__(self, model: str):
        self.client = anthropic.Anthropic()
        self.model = model

    def generate_json(self, system: str, prompt: str, schema: dict, max_tokens: int = 8000) -> dict:
        """JSONスキーマに従った構造化出力を返す。"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            thinking={"type": "adaptive"},
            output_config={"format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": prompt}],
        )
        if response.stop_reason == "max_tokens":
            raise RuntimeError("出力がmax_tokensに達しました。設定を見直してください。")
        text = next(b.text for b in response.content if b.type == "text")
        return json.loads(text)

    def generate_text(self, system: str, prompt: str, max_tokens: int = 32000) -> str:
        """長文(記事本文など)をストリーミングで生成して全文を返す。"""
        with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            message = stream.get_final_message()
        if message.stop_reason == "max_tokens":
            raise RuntimeError("出力がmax_tokensに達しました。設定を見直してください。")
        return "".join(b.text for b in message.content if b.type == "text")
