# Model identity caveat

The Fin-o1 experiment artifacts do not contain enough metadata to establish the
exact answer-generator checkpoint from the result files alone.

The two selected directories are:

- `results/latest/mc-fino-30b-latest`
- `results/latest/finbench-fino-30b-latest`

Their names contain `30b`, while historical plotting code labeled the model
`Fino1-8B` and a historical smoke-test script targets
`TheFinAI/Fino1-8B`. Public plotting code now uses a size-neutral `Fin-o1`
label. Neither `results.jsonl` nor `summary.json` records a model identifier,
revision, inference provider, or decoding configuration. A directory name or
plot label is not sufficient provenance.

Recover the run configuration from the original command, job log, provider
request record, or immutable model-service deployment. The generated
`run_manifest.json` files currently record these fields as unavailable; replace
the explicit gaps with at least:

```json
{
  "model_id": "REQUIRED",
  "model_revision": "REQUIRED",
  "parameter_count_label": "REQUIRED",
  "inference_provider": "REQUIRED",
  "endpoint_or_engine_version": "REQUIRED",
  "decoding": {
    "temperature": "REQUIRED",
    "top_p": "REQUIRED",
    "max_tokens": "REQUIRED",
    "seed": "REQUIRED_OR_NULL"
  },
  "prompt_template_sha256": "REQUIRED",
  "dataset_sha256": "REQUIRED",
  "verifier_config_sha256": "REQUIRED"
}
```

Until that evidence is recovered, public manifests and tables should use a
neutral label such as **Fin-o1 (checkpoint identity pending)**. Do not silently
choose 8B or 30B from the conflicting filenames.

The same general rule applies to directories named `latest`: the public bundle
must identify an immutable source path and checksums. In particular, the two
Qwen3 alternatives documented in `README.md` are distinct runs, not aliases.
