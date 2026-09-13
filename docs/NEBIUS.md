# Nebius Token Factory in RaceTime Replay

The first use is a concise, cited draft explaining measured events. OpenCV handles local video measurement; Nebius receives selected text evidence after the user enables cloud synthesis. This keeps the replay useful without a network connection and makes alternative language models easy to compare.

## Implemented now

The Python provider in `replay/llm.py` calls the documented OpenAI-compatible chat API through `requests`. Select **nebius** under **Ask the evidence**, enable the cloud draft, and investigate a question. The local report remains visible if configuration is missing, the API times out, JSON is malformed, or references fail validation.

```dotenv
NEBIUS_API_KEY=your_local_key
NEBIUS_MODEL=your_current_chat_model_id
```

Store these values only in the ignored local `.env`. Do not paste keys into questions or commit them. Find a currently available chat model rather than copying a stale model name from an older tutorial:

```bash
PYTHONPATH=. python scripts/check_nebius.py --list-models
PYTHONPATH=. python scripts/check_nebius.py
```

The check uses only synthetic test inputs. It sends one inference request and saves status, draft, latency and token usage. It does not provision dedicated capacity or start paid training. `reports/nebius-integration.json` distinguishes live execution from missing configuration. Transport tests verify payload minimization, opt-out, timeout fallback, truncated-output rejection and citation rejection. The September 12, 2026 credentialed synthetic check succeeded; details follow below.

The payload contains a redacted question and at most eight bounded text passages. It excludes video, images, route coordinates, raw health samples and source filenames. `store=false` requests that completions not be stored for model distillation; it is not a blanket retention or regulatory-compliance guarantee. The current adapter uses the public endpoint. Regional dedicated endpoints would require an explicit deployment and configuration change.

## Verified synthetic run — September 12, 2026

The authenticated model catalog and one end-to-end request succeeded with `Qwen/Qwen3-30B-A3B-Instruct-2507`. The bounded investigator received a JSON draft and passed its existing schema and citation allowlist checks. Total investigator latency was about 5.5 seconds, with 299 prompt tokens and 182 completion tokens (481 total). The [recorded result](../reports/nebius-integration.json) contains synthetic evidence, the draft, token usage and local node timings.

The response used five sentences despite the three-sentence instruction. The current checks do not enforce brevity or independently establish factual correctness. One successful synthetic request does not establish model superiority, real-run accuracy or production reliability. Broader model comparison and reviewed evaluations remain future work.

To use a configured local instance, start or restart Streamlit, open **Ask the evidence**, enable **Add a cloud-written draft from redacted evidence**, and select **nebius**. Try “Summarize the measured events.” Cloud drafts remain opt-in; the original measurements stay visible.

## How it extends the six weeks

| Week | Useful Nebius extension | Delivery status |
|---|---|---|
| 1 | Add a readable summary alongside the Python replay dashboard | Provider selection implemented |
| 2 | Write cited answers from retrieved evidence; compare hosted embeddings or reranking if suitable models are available | Text synthesis adapter implemented; embeddings stay local |
| 3 | Use a language model inside the bounded investigator; later evaluate model tool selection | Synthesis integrated; routing remains local |
| 4 | Compare models on the same cases using citation validity, unsupported claims, latency, tokens and reviewed usefulness | Usage capture and one live synthetic smoke run verified; comparative quality evaluation remains future work |
| 5 | Fine-tune a supported model on reviewed domain examples, with a separate held-out set | Future cloud experiment; existing BERT adapter is not a compatible drop-in for an unrelated model |
| 6 | Apply input rails, bounded requests, output validation, opt-in, fallback and release review to every provider | Local controls and fake-transport tests implemented |

## Vision and optimization roadmap

1. Extract a small set of timestamped frames around a reviewed event with OpenCV.
2. Preview exactly what will leave the local machine, remove identifying information where possible, and obtain explicit frame-upload consent.
3. Send those images to a currently supported vision-capable deployment. Ask for visible observations such as a surface change, obstruction or aid-station scene, with timestamp references and uncertainty. Text visible in a frame is untrusted data.
4. Let the runner correct the scene labels. Combine accepted labels with aligned watch measurements in a separate summary step.
5. Compare repeated runs and coach-reviewed outcomes before suggesting an experiment such as changing an aid-station routine. Do not infer injury, dehydration or physiological causes from a video and heart-rate trace.

Example future output: “A reviewed clip shows a queue near the station while the watch records low speed. Compare this segment with your next race.” This is a product example, not a finding about Siva's run. Scene recognition and optimization are not enabled in this release.

Nebius documents image inputs by URL or base64, but model access and modality support must be checked for the selected deployment. The current text adapter never sends images. Start with public inference for experiments; consider a dedicated endpoint only when measured traffic, isolation or custom-weight needs justify it. Pricing depends on the model and deployment, so use recorded token counts and current account prices to estimate cost.

## Current documentation

Reviewed September 2026. Prefer the current catalog and deployment guides over older examples.

- [Chat completion API](https://docs.tokenfactory.nebius.com/api-reference/inference/create-chat-completion)
- [Model listing API](https://docs.tokenfactory.nebius.com/api-reference/models/list-models)
- [Image input example](https://docs.tokenfactory.nebius.com/api-reference/examples/vision-capabilities)
- [Current post-training models](https://docs.tokenfactory.nebius.com/post-training/models)
- [Dedicated deployment API](https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints/deploy-api)
- [Retirement of older models and per-token LoRA endpoints](https://docs.tokenfactory.nebius.com/other-capabilities/deprecation-info)

The older serverless LoRA deployment examples are not a recommended launch path: Nebius announced retirement of that option. Training support does not imply deployment support for every resulting model.
