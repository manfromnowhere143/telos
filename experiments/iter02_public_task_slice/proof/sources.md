# Sources

## CodeClash

- Repository: <https://github.com/codeclash-ai/codeclash>
- Local inspected commit: `381cdfa05a35e8acd35853b9fc7e13005121b127`
- License: MIT, inspected from `LICENSE`
- Selected config: `configs/test/dummy.yaml`
- Documentation note: CodeClash docs describe `configs/test/` as smoke tests with dummy agents and
  no LLM API calls.

## SWE-bench Verified

- Dataset page: <https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified>
- Dataset HEAD observed by public API: `91aa3ed51b709be6457e12d00300a6a596d4c6a3`
- Benchmark page: <https://www.swebench.com/verified.html>
- Rows API used for the supporting row:
  <https://datasets-server.huggingface.co/rows?dataset=SWE-bench%2FSWE-bench_Verified&config=default&split=test&offset=0&length=1>

Pinned supporting task:

```text
astropy__astropy-12907
```

Pinned hashes:

```text
problem_statement_sha256: c01334ec1b21a089c650cf2e7b96ab974469076bf1260d23885799e1f0a7551f
patch_sha256: 0f3e44432ed8540e9526edff4f83793948a2f139fc3971b67c30043c1eb7964a
test_patch_sha256: 5ef90b640ffce4590bb61ef2ea0e3256416dddf41b45bf4f2c3610a6e8c53718
```

The canonical field names are kept in `slice.json`.
