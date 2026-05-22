#!/usr/bin/env python3.11
"""
============================================================
 NVIDIA ShadowForge - Teste de Conexao API NVIDIA NIM
 Arquivo: tests/test_api_nvidia.py
============================================================
 Verifica conexao com a API NVIDIA NIM e testa
 diferentes modelos disponiveis.
============================================================
"""

import asyncio
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    pass

try:
    from rich.console import Console
    from rich.table import Table
    console = Console(force_terminal=True)
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


async def test_nim_connection():
    import aiohttp

    key = os.environ.get("NVIDIA_API_KEY", "")
    base_url = "https://integrate.api.nvidia.com/v1"

    results = []

    # Step 1: Listar modelos
    async with aiohttp.ClientSession(
        headers={"Authorization": f"Bearer {key}"},
        timeout=aiohttp.ClientTimeout(total=15)
    ) as session:
        # Lista modelos
        async with session.get(f"{base_url}/models") as resp:
            if resp.status == 200:
                data = await resp.json()
                models = [m["id"] for m in data.get("data", [])]
                results.append(("GET /models", True, f"{len(models)} modelos disponiveis"))
            else:
                text = await resp.text()
                results.append(("GET /models", False, f"Erro {resp.status}: {text[:80]}"))
                models = []

        # Testa modelos que funcionam com a API key do usuario
        test_models = [
            ("meta/llama-3.3-70b-instruct", "Planejamento/Raciocinio"),
            ("meta/llama-3.2-90b-vision-instruct", "Visao"),
            ("meta/llama-3.1-8b-instruct", "Codigo/Fallback"),
            ("meta/llama-3.2-11b-vision-instruct", "Multimodal"),
            ("meta/llama-3.2-3b-instruct", "Rapido/Leve"),
            ("google/gemma-2-2b-it", "Alternativo Gemma"),
        ]

        for model_id, purpose in test_models:
            if model_id not in models:
                results.append((f"CHAT {model_id}", False, "Modelo nao listado"))
                continue

            try:
                payload = {
                    "model": model_id,
                    "messages": [{"role": "user", "content": "Responda apenas: OK"}],
                    "max_tokens": 10,
                    "temperature": 0.1,
                }
                async with session.post(
                    f"{base_url}/chat/completions",
                    json=payload
                ) as resp2:
                    if resp2.status == 200:
                        data2 = await resp2.json()
                        content = data2.get("choices", [{}])[0].get("message", {}).get("content", "")
                        results.append((f"CHAT {model_id}", True, f"OK - [{purpose}] Resposta: {content[:30]}"))
                    else:
                        text = await resp2.text()
                        results.append((f"CHAT {model_id}", False, f"Erro {resp2.status}: {text[:80]}"))
            except Exception as e:
                results.append((f"CHAT {model_id}", False, f"Excecao: {str(e)[:60]}"))

    return results


def main():
    print("\n" + "=" * 60)
    print("  NVIDIA ShadowForge - Teste API NIM")
    print("=" * 60 + "\n")

    key = os.environ.get("NVIDIA_API_KEY", "")
    if not key:
        print("  [FALHA] NVIDIA_API_KEY nao configurada no .env")
        return 1

    print(f"  API Key: {key[:12]}...{key[-6:]}")
    print()

    results = asyncio.run(test_nim_connection())

    if HAS_RICH:
        table = Table(title="Resultados API NVIDIA NIM", show_header=True, header_style="bold cyan")
        table.add_column("Teste", style="cyan", width=45)
        table.add_column("Status", width=10)
        table.add_column("Detalhe", style="dim")
        for test_name, ok, detail in results:
            status = "[green]OK[/green]" if ok else "[red]FALHA[/red]"
            table.add_row(test_name, status, detail)
        console.print(table)
    else:
        for test_name, ok, detail in results:
            status = "OK" if ok else "FALHA"
            print(f"  {test_name:45s} {status:10s} {detail}")

    ok_count = sum(1 for _, ok, _ in results if ok)
    print(f"\n  Resultado: {ok_count}/{len(results)} testes OK\n")

    return 0 if ok_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
